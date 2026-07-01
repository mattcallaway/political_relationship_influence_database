# apps/extraction/cataloger.py
import re
import logging
from django.utils import timezone
from django.db import transaction

from apps.entities.models import Entity, Person, Organization, Alias, EntityType, EntityStatus
from apps.transactions.models import Contribution, ReviewStatus
from apps.extraction.models import ExtractedContributorBlock, EntityMatchAttempt, EntityMatchCandidate
from apps.extraction.matcher import find_best_entity_match, normalize_text, get_competing_candidates

logger = logging.getLogger(__name__)

def generate_next_public_id(prefix):
    """
    Generates a sequential public ID matching existing formats.
    e.g. P000011, ORG000004, CON000001
    """
    count = Entity.objects.filter(public_id__startswith=prefix).count()
    if prefix == 'CON':
        count = Contribution.objects.count()
        
    for attempt in range(1, 100):
        pub_id = f"{prefix}{(count + attempt):06d}"
        if prefix == 'CON':
            if not Contribution.objects.filter(public_id=pub_id).exists():
                return pub_id
        else:
            if not Entity.objects.filter(public_id=pub_id).exists():
                return pub_id
    return f"{prefix}_unknown"

def get_or_create_filer_entity(filer_name, committee_id=None):
    """
    Finds or creates a proposed/approved entity for the campaign filer.
    """
    if not filer_name:
        return None
        
    if committee_id:
        org = Organization.objects.filter(committee_id=committee_id).first()
        if org:
            return org.entity
            
    entity = Entity.objects.filter(canonical_name__iexact=filer_name).first()
    if entity:
        return entity
        
    alias = Alias.objects.filter(alias_text__iexact=filer_name).first()
    if alias:
        return alias.entity
        
    # Create new Organization
    pub_id = generate_next_public_id('ORG')
    entity = Entity.objects.create(
        public_id=pub_id,
        canonical_name=filer_name,
        entity_type=EntityType.ORGANIZATION,
        status=EntityStatus.PROVISIONAL_AUTO_CREATED
    )
    Organization.objects.create(
        entity=entity,
        legal_name=filer_name,
        committee_id=committee_id or ""
    )
    Alias.objects.create(
        entity=entity,
        alias_text=filer_name,
        normalized_alias=filer_name.lower().strip()
    )
    return entity

def catalog_contributor_block(record, page, import_batch=None, session_cache=None):
    """
    Parses, deduplicates, matches, and catalogs an extracted contributor block.
    Saves all details directly to the central database.
    
    session_cache: dictionary to cache provisional entities created in this batch
                   to prevent batch-level duplicates.
    """
    donor_name = record.get("contributor_name", "").strip()
    donor_code = record.get("contributor_code", "IND")
    occupation = record.get("occupation", "").strip()
    employer = record.get("employer", "").strip()
    city = record.get("city", "").strip()
    state = record.get("state", "").strip()
    zip_code = record.get("zip_code", "").strip()
    
    if not donor_name:
        return None
        
    is_person = (donor_code == "IND")
    etype = EntityType.PERSON if is_person else EntityType.ORGANIZATION
    prefix = 'P' if is_person else 'ORG'
    
    # Check session_cache for batch-level deduplication clustering
    cache_key = f"{normalize_text(donor_name)}_{normalize_text(city)}_{normalize_text(occupation)}"
    matched_entity = None
    match_method = "NEW_PROVISIONAL_ENTITY"
    
    if session_cache is not None and cache_key in session_cache:
        matched_entity = session_cache[cache_key]
        match_method = "BATCH_DEDUPLICATED"
        logger.info(f"Batch deduplication: Clustered '{donor_name}' to existing batch provisional entity {matched_entity.public_id}")
        
    # Execute matcher if not resolved in current batch cache
    if not matched_entity:
        matched_entity, match_method, match_metrics, candidates = find_best_entity_match(
            donor_name, donor_code, occupation, employer, city, state, zip_code
        )
        
    # Determine the review and entity statuses
    entity_status = EntityStatus.PROVISIONAL_AUTO_CREATED
    con_status = ReviewStatus.AUTO_IMPORTED
    
    if matched_entity:
        # High confidence match thresholds
        if match_method in ("EXACT_COMMITTEE_ID", "EXACT_NORMALIZED_NAME", "EXACT_ALIAS") or (
            match_method in ("NAME_AND_LOCATION", "NAME_AND_EMPLOYMENT", "HIGH_CONFIDENCE_FUZZY") and match_metrics.get("score", 0) >= 95.0
        ):
            con_status = ReviewStatus.AUTO_MATCHED
            # Only elevate status if it was not already provisional
            if matched_entity.status == EntityStatus.PROVISIONAL_AUTO_CREATED:
                matched_entity.status = EntityStatus.AUTO_MATCHED
                matched_entity.save()
        else:
            con_status = ReviewStatus.NEEDS_REVIEW
    else:
        # Create a new PROVISIONAL_AUTO_CREATED Entity
        with transaction.atomic():
            pub_id = generate_next_public_id(prefix)
            matched_entity = Entity.objects.create(
                public_id=pub_id,
                canonical_name=donor_name,
                entity_type=etype,
                status=EntityStatus.PROVISIONAL_AUTO_CREATED
            )
            Alias.objects.create(
                entity=matched_entity,
                alias_text=donor_name,
                normalized_alias=normalize_text(donor_name)
            )
            
            if is_person:
                parts = donor_name.split(",")
                if len(parts) == 2:
                    last = parts[0].strip()
                    first = parts[1].strip()
                else:
                    parts = donor_name.split()
                    first = parts[0].strip() if len(parts) > 0 else ""
                    last = parts[-1].strip() if len(parts) > 1 else ""
                    
                Person.objects.create(
                    entity=matched_entity,
                    display_name=donor_name,
                    first_name=first,
                    last_name=last,
                    occupation=occupation,
                    notes=f"Employer: {employer}" if employer else ""
                )
            else:
                committee_id = ""
                id_match = re.search(r'(?:ID#|I.D. NUMBER)\s*(\d+)', donor_name, re.IGNORECASE)
                if id_match:
                    committee_id = id_match.group(1)
                Organization.objects.create(
                    entity=matched_entity,
                    legal_name=donor_name,
                    committee_id=committee_id
                )
                
        # Cache for batch-level deduplication
        if session_cache is not None:
            session_cache[cache_key] = matched_entity

    # Get or create Filer Committee Entity
    filer_entity = get_or_create_filer_entity(record.get("committee_name"), record.get("committee_id"))
    
    # Save the ExtractedContributorBlock record
    ext_block = ExtractedContributorBlock.objects.create(
        page=page,
        block_number=record.get("visual_block_number", 1),
        raw_text=record.get("raw_block_text", ""),
        bounding_box_json=record.get("bounding_box", []),
        extraction_method="embedded_text_layout" if page.document.has_native_text else "OCR_layout",
        parser_version="2.0",
        original_parsed_json=record
    )
    
    # Create the Contribution record
    con_pub_id = generate_next_public_id('CON')
    
    # Parse Date
    date_val = None
    date_str = record.get("date")
    if date_str:
        try:
            import datetime
            parts = date_str.split("/")
            if len(parts) == 3:
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100:
                    year += 2000
                date_val = datetime.date(year, month, day)
        except Exception:
            pass

    con = Contribution.objects.create(
        public_id=con_pub_id,
        filer_committee=filer_entity,
        donor_entity=matched_entity,
        donor_raw_name=donor_name,
        transaction_date=date_val,
        amount=record.get("amount", 0.0),
        cumulative_amount=record.get("cumulative_calendar_year_amount"),
        schedule='Schedule A',
        transaction_code=donor_code,
        occupation=occupation,
        employer=employer,
        city_state_zip=f"{city}, {state} {zip_code}".strip(),
        document_page=page,
        document=page.document,
        extracted_block=ext_block,
        import_batch=import_batch,
        review_status=con_status
    )
    
    # Record the Match Attempt
    if match_method != "BATCH_DEDUPLICATED":
        attempt = EntityMatchAttempt.objects.create(
            contribution=con,
            selected_entity=matched_entity,
            match_method=match_method,
            match_score=match_metrics.get("score", 0.0),
            name_score=match_metrics.get("name_score", 0.0),
            location_score=match_metrics.get("location_score", 0.0),
            employer_score=match_metrics.get("employer_score", 0.0),
            entity_type_compatibility=match_metrics.get("entity_type_compatibility", True),
            committee_id_match=match_metrics.get("committee_id_match", False),
            reason=match_metrics.get("reason", ""),
            model_version="2.0"
        )
        
        # Link match attempt to contribution
        con.match_attempt = attempt
        con.save()
        
        # Record Competing Candidates
        for c in candidates[:5]: # Store top 5 candidates only
            EntityMatchCandidate.objects.create(
                match_attempt=attempt,
                entity=c["entity"],
                score=c["score"],
                match_method=c["method"]
            )
            
    return con
