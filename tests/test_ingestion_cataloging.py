# tests/test_ingestion_cataloging.py
import json
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentPage, DocumentProcessingStatus
from apps.documents.services import process_document_pdf
from apps.entities.models import Entity, Person, Organization, Alias, EntityStatus, EntityMerge
from apps.transactions.models import Contribution, ReviewStatus, AuditEvent
from apps.extraction.models import ExtractedContributorBlock, EntityMatchAttempt, EntityMatchCandidate
from apps.extraction.services import parse_form_460
from apps.extraction.cataloger import catalog_contributor_block

User = get_user_model()

@pytest.fixture
def test_user():
    return User.objects.create_user(username='reviewer_test', password='password')

@pytest.fixture
def sample_setup():
    # Setup document, page, and batch
    from apps.audit.models import ImportBatch
    batch = ImportBatch.objects.create(batch_name="Test Batch Ingestion", source_file="sample.pdf")
    
    doc = Document.objects.create(
        original_filename="Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf",
        file_path="Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf",
        sha256_hash="dummy_hash_gore_2026",
        byte_size=1000,
        media_type="application/pdf",
        processing_status=DocumentProcessingStatus.EXTRACTION_COMPLETE
    )
    
    page = DocumentPage.objects.create(
        document=doc,
        page_number=4,
        extracted_text="SCHEDULE A",
        processing_status='COMPLETED'
    )
    
    return doc, page, batch

@pytest.mark.django_db
def test_exact_committee_id_auto_match(sample_setup):
    doc, page, batch = sample_setup
    
    # Create canonical committee
    committee = Entity.objects.create(
        public_id="ORG000001",
        canonical_name="Agricultural Council of CA Issues PAC",
        entity_type="ORGANIZATION",
        status=EntityStatus.APPROVED
    )
    Organization.objects.create(
        entity=committee,
        legal_name="Agricultural Council of CA Issues PAC",
        committee_id="1280428"
    )
    
    # Ingest record with ID match
    record = {
        "committee_name": "Friends of James Gore",
        "committee_id": "1456999",
        "contributor_name": "Agricultural Council of CA Issues PAC (ID# 1280428)",
        "contributor_code": "OTH",
        "date": "10/23/2023",
        "amount": 50000.0,
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95814",
        "visual_block_number": 1,
        "raw_block_text": "Agricultural Council of CA Issues PAC (ID# 1280428) OTH 50,000.00"
    }
    
    con = catalog_contributor_block(record, page, import_batch=batch)
    assert con.donor_entity == committee, "Should auto-link to matching committee ID"
    assert con.review_status == ReviewStatus.AUTO_MATCHED

@pytest.mark.django_db
def test_exact_normalized_name_auto_match(sample_setup):
    doc, page, batch = sample_setup
    
    person = Entity.objects.create(
        public_id="P000001",
        canonical_name="Joshua Hochberg",
        entity_type="PERSON",
        status=EntityStatus.APPROVED
    )
    Person.objects.create(entity=person, display_name="Joshua Hochberg")
    
    record = {
        "committee_name": "Friends of James Gore",
        "contributor_name": "joshua hochberg", # lowercase
        "contributor_code": "IND",
        "date": "10/23/2023",
        "amount": 2500.0,
        "visual_block_number": 1
    }
    
    con = catalog_contributor_block(record, page, import_batch=batch)
    assert con.donor_entity == person, "Should auto-link to exact normalized name"
    assert con.review_status == ReviewStatus.AUTO_MATCHED

@pytest.mark.django_db
def test_high_confidence_fuzzy_auto_match(sample_setup):
    doc, page, batch = sample_setup
    
    person = Entity.objects.create(
        public_id="P000002",
        canonical_name="Charles Sweeney",
        entity_type="PERSON",
        status=EntityStatus.APPROVED
    )
    Person.objects.create(entity=person, display_name="Charles Sweeney")
    
    # Slight variation: Charles Sweeny (score >= 95%)
    record = {
        "committee_name": "Friends of James Gore",
        "contributor_name": "Charles Sweeny",
        "contributor_code": "IND",
        "date": "12/05/2023",
        "amount": 3500.0,
        "visual_block_number": 1
    }
    
    con = catalog_contributor_block(record, page, import_batch=batch)
    assert con.donor_entity == person, "Should auto-link on high fuzzy similarity score"
    assert con.review_status == ReviewStatus.AUTO_MATCHED

@pytest.mark.django_db
def test_ambiguous_fuzzy_creates_provisional(sample_setup):
    doc, page, batch = sample_setup
    
    person = Entity.objects.create(
        public_id="P000003",
        canonical_name="John Smith",
        entity_type="PERSON",
        status=EntityStatus.APPROVED
    )
    Person.objects.create(entity=person, display_name="John Smith")
    
    # Name variation (John R. Smith: low/medium similarity)
    record = {
        "committee_name": "Friends of James Gore",
        "contributor_name": "John R. Smith",
        "contributor_code": "IND",
        "date": "12/05/2023",
        "amount": 100.0,
        "visual_block_number": 1
    }
    
    con = catalog_contributor_block(record, page, import_batch=batch)
    assert con.donor_entity != person, "Should not link low/medium fuzzy match without metadata"
    assert con.donor_entity.status == EntityStatus.PROVISIONAL_AUTO_CREATED
    assert con.review_status == ReviewStatus.AUTO_IMPORTED

@pytest.mark.django_db
def test_batch_deduplication_clusters_provisional(sample_setup):
    doc, page, batch = sample_setup
    session_cache = {}
    
    record1 = {
        "committee_name": "Friends of James Gore",
        "contributor_name": "Unique Donor Name",
        "contributor_code": "IND",
        "date": "10/10/2023",
        "amount": 100.0,
        "city": "Windsor",
        "visual_block_number": 1
    }
    
    record2 = {
        "committee_name": "Friends of James Gore",
        "contributor_name": "Unique Donor Name",
        "contributor_code": "IND",
        "date": "10/15/2023",
        "amount": 200.0,
        "city": "Windsor",
        "visual_block_number": 2
    }
    
    con1 = catalog_contributor_block(record1, page, import_batch=batch, session_cache=session_cache)
    con2 = catalog_contributor_block(record2, page, import_batch=batch, session_cache=session_cache)
    
    assert con1.donor_entity == con2.donor_entity, "Repeated provisional transactions in batch must cluster to the same entity"

@pytest.mark.django_db
def test_reviewer_confirms_match(sample_setup, test_user):
    doc, page, batch = sample_setup
    
    person = Entity.objects.create(
        public_id="P000004",
        canonical_name="Confirm Person",
        entity_type="PERSON",
        status=EntityStatus.PROVISIONAL_AUTO_CREATED
    )
    
    con = Contribution.objects.create(
        public_id="CON999001",
        filer_committee=person,
        donor_entity=person,
        donor_raw_name="Confirm Person",
        amount=100.0,
        review_status=ReviewStatus.AUTO_IMPORTED,
        document=doc
    )
    
    from apps.extraction.views import confirm_match
    from unittest.mock import Mock
    request = Mock()
    request.method = "POST"
    request.user = test_user
    
    confirm_match(request, con.id)
    
    con.refresh_from_db()
    person.refresh_from_db()
    
    assert con.review_status == ReviewStatus.VERIFIED
    assert person.status == EntityStatus.VERIFIED
    
    # Audit log check
    audit = AuditEvent.objects.filter(action="MATCH_CONFIRMED", record_id=str(con.id)).first()
    assert audit is not None
    assert audit.user == test_user

@pytest.mark.django_db
def test_reviewer_overrides_match(sample_setup, test_user):
    doc, page, batch = sample_setup
    
    entity_a = Entity.objects.create(public_id="P000005", canonical_name="Wrong Person", entity_type="PERSON")
    entity_b = Entity.objects.create(public_id="P000006", canonical_name="Correct Person", entity_type="PERSON")
    
    con = Contribution.objects.create(
        public_id="CON999002",
        filer_committee=entity_a,
        donor_entity=entity_a,
        donor_raw_name="Correct Person",
        amount=150.0,
        review_status=ReviewStatus.AUTO_MATCHED,
        document=doc
    )
    
    from apps.extraction.views import rematch_contribution
    from unittest.mock import Mock
    request = Mock()
    request.method = "POST"
    request.user = test_user
    request.POST = {"target_entity": str(entity_b.id), "reason": "Wrong auto link."}
    
    rematch_contribution(request, con.id)
    
    con.refresh_from_db()
    assert con.donor_entity == entity_b, "Override should link transaction to corrected entity"
    
    # Audit event logged
    audit = AuditEvent.objects.filter(action="MATCH_OVERRIDDEN", record_id=str(con.id)).first()
    assert audit is not None
    assert audit.new_value["donor_entity_id"] == str(entity_b.id)

@pytest.mark.django_db
def test_entity_merge_workflow(sample_setup, test_user):
    doc, page, batch = sample_setup
    
    canonical = Entity.objects.create(public_id="P000007", canonical_name="Canonical Entity", entity_type="PERSON", status=EntityStatus.VERIFIED)
    provisional = Entity.objects.create(public_id="P000008", canonical_name="Provisional Entity", entity_type="PERSON", status=EntityStatus.PROVISIONAL_AUTO_CREATED)
    
    con = Contribution.objects.create(
        public_id="CON999003",
        filer_committee=canonical,
        donor_entity=provisional,
        donor_raw_name="Provisional Entity",
        amount=500.0,
        document=doc
    )
    
    from apps.extraction.views import merge_entities
    from unittest.mock import Mock
    request = Mock()
    request.method = "POST"
    request.user = test_user
    request.POST = {"target_entity": str(canonical.id), "reason": "Identical person.", "document_id": str(doc.id)}
    
    merge_entities(request, provisional.id)
    
    con.refresh_from_db()
    provisional.refresh_from_db()
    
    assert con.donor_entity == canonical, "Transactions must reassign to canonical entity"
    assert provisional.status == EntityStatus.MERGED, "Provisional entity status must set to MERGED"
    
    # Alias added to canonical
    alias = Alias.objects.filter(entity=canonical, alias_text="Provisional Entity").first()
    assert alias is not None
    
    # Merge history preserved
    merge = EntityMerge.objects.filter(source_entity=provisional, target_entity=canonical).first()
    assert merge is not None

@pytest.mark.django_db
def test_reprocessing_protections():
    # Ingest document
    pdf_path = r'data\uploads\documents\2026\06\Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf'
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
        
    uploaded_file = SimpleUploadedFile(
        name="Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf",
        content=file_data,
        content_type='application/pdf'
    )
    
    doc = Document.objects.create(
        original_filename=uploaded_file.name,
        file_path=uploaded_file,
        byte_size=len(file_data),
        sha256_hash="hash_reprocess_test",
        media_type='application/pdf',
        processing_status=DocumentProcessingStatus.UPLOADED
    )
    
    process_document_pdf(doc.id)
    parse_form_460(doc)
    
    # Set one parsed contribution to verified status
    con = Contribution.objects.filter(document=doc, extracted_block__block_number=1).first()
    con.review_status = ReviewStatus.VERIFIED
    con.donor_raw_name = "Reviewer Verified Name"
    con.save()
    
    # Run reprocessing (re-parsing document)
    parse_form_460(doc)
    
    # Verify that reprocessing preserved the verified contribution
    con_after = Contribution.objects.filter(document=doc, extracted_block__block_number=1).first()
    assert con_after.review_status == ReviewStatus.VERIFIED
    assert con_after.donor_raw_name == "Reviewer Verified Name", "Reprocessing should not overwrite reviewer-approved record"
