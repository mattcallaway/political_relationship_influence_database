# apps/extraction/services.py
import re
import json
import logging
from difflib import SequenceMatcher
from django.utils import timezone

from apps.extraction.models import ExtractionJob, ExtractedField, FieldReviewStatus
from apps.entities.models import Entity
from apps.documents.models import Document, DocumentPage

logger = logging.getLogger(__name__)

def words_to_lines(words, vy_threshold=4.0):
    """
    Groups visual words into lines based on their vertical coordinates (vy0).
    Sorts lines from top to bottom, and words within each line from left to right.
    """
    if not words:
        return []
    
    # Sort words by vy0 first
    sorted_words = sorted(words, key=lambda w: w["vy0"])
    
    lines = []
    current_line = []
    current_vy = None
    
    for w in sorted_words:
        vy = w["vy0"]
        if current_vy is None:
            current_vy = vy
            current_line.append(w)
        elif abs(vy - current_vy) <= vy_threshold:
            current_line.append(w)
        else:
            # Sort current line from left to right (vx0)
            current_line.sort(key=lambda x: x["vx0"])
            lines.append(current_line)
            current_line = [w]
            current_vy = vy
            
    if current_line:
        current_line.sort(key=lambda x: x["vx0"])
        lines.append(current_line)
        
    # Convert list of word dicts to line strings
    line_strings = []
    for line in lines:
        line_strings.append(" ".join([w["text"] for w in line]))
    return line_strings

def clean_amount(val_str):
    """
    Extracts a numeric float value from amount strings, retaining negative sign.
    Handles parentheses like (1,000.00) as negative.
    """
    if not val_str:
        return 0.0
    val_str = val_str.strip()
    
    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1]
        
    # Match the first floating-point or integer number in the string
    match = re.search(r'[-+]?[\d,]+\.?\d*', val_str)
    if not match:
        return 0.0
        
    cleaned = match.group(0).replace(",", "")
    try:
        val = float(cleaned)
        return -val if is_negative else val
    except ValueError:
        return 0.0

def parse_form_460(document):
    """
    Main ingestion pipeline entry point for Form 460 extraction.
    Uses layout-first geometric parsing for born-digital files,
    and simulated layout-first OCR processing for scanned files.
    """
    from apps.audit.models import ImportBatch
    batch, _ = ImportBatch.objects.get_or_create(
        batch_name=f"Filing_Extraction_{document.id}",
        defaults={'source_file': document.original_filename, 'status': 'COMPLETED'}
    )
    session_cache = {}

    job = ExtractionJob.objects.create(
        document=document,
        job_type='FORM_460_PARSER',
        processing_engine='Two-Pass Visual Coordinate Parser',
        engine_version='2.0',
        status='RUNNING'
    )
    
    try:
        from apps.extraction.geometry import get_visual_width_height, get_visual_rect
        from apps.extraction.segmenter import segment_page_into_blocks
        from apps.extraction.checkbox_detector import detect_checkbox_digital
        from apps.extraction.validation import validate_contribution_record
        from apps.extraction.ocr_preprocessor import perform_ocr_on_page
        
        # We process each page of the document
        for page in document.pages.all():
            text = page.extracted_text or ""
            
            # Check if this page is a Schedule A page
            schedule_a_indicators = ("SCHEDULE A", "MONETARY CONTRIBUTIONS", "FULL NAME", "CONTRIBUTOR CODE")
            is_schedule_a = any(ind in text.upper() for ind in schedule_a_indicators)
            
            # For scanned pages (empty text), check the page index or fall back to OCR
            if not is_schedule_a and len(text.strip()) < 10:
                # Run OCR preprocessor to retrieve words with coordinates
                words = perform_ocr_on_page(document.file_path.path, page.page_number, original_filename=document.original_filename)
                if words:
                    is_schedule_a = True
            else:
                # Born digital
                import fitz
                doc_fitz = fitz.open(document.file_path.path)
                page_fitz = doc_fitz[page.page_number - 1]
                words = page_fitz.get_text("words")
                
            if not is_schedule_a:
                continue
                
            rotation = 90  # Default rotation for landscape NetFile PDFs
            try:
                import fitz
                doc_fitz = fitz.open(document.file_path.path)
                rotation = doc_fitz[page.page_number - 1].rotation
            except Exception:
                pass
                
            page_width = 612.0
            page_height = 792.0
            try:
                import fitz
                doc_fitz = fitz.open(document.file_path.path)
                page_fitz = doc_fitz[page.page_number - 1]
                rect_fitz = page_fitz.rect
                
                # Unrotated dimensions
                if rotation in (90, 270):
                    page_width, page_height = rect_fitz.height, rect_fitz.width
                else:
                    page_width, page_height = rect_fitz.width, rect_fitz.height
                    
                # Normalize landscape pages of rotation 0 to rotation 90
                if rotation == 0 and page_width > page_height:
                    rotation = 90
                    page_width, page_height = page_height, page_width
            except Exception:
                pass
                
            # Segment the page into visual contributor blocks
            blocks = segment_page_into_blocks(words, rotation, page_width, page_height)
            
            # Read filer metadata from the top header
            # Filer Name is usually visually located around vx in [100, 760], vy in [90, 130]
            filer_name = ""
            committee_id = ""
            for w in words:
                rect = (w[0], w[1], w[2], w[3])
                vx0, vy0, vx1, vy1 = get_visual_rect(rect, rotation, page_width, page_height)
                if 90 <= vy0 <= 130:
                    if 100 <= vx0 <= 600:
                        filer_name += " " + w[4]
                    elif 600 < vx0 <= 770:
                        committee_id += w[4]
            filer_name = filer_name.strip()
            committee_id = re.sub(r'\D', '', committee_id) # Numeric only
            
            # Robust fallback to document filename if visual header parse is empty
            if not filer_name:
                base_name = document.original_filename
                if "_fppc460" in base_name:
                    filer_name = base_name.split("_fppc460")[0].replace("_", " ").strip()
                elif "fppc460" in base_name:
                    filer_name = base_name.split("fppc460")[0].replace("_", " ").strip()
            
            # Process each visual contributor block
            for b in blocks:
                # Reprocessing Protection
                from apps.transactions.models import Contribution, ReviewStatus
                existing_con = Contribution.objects.filter(
                    document=document,
                    document_page=page,
                    extracted_block__block_number=b["block_number"]
                ).first()
                if existing_con:
                    if existing_con.review_status in ('REVIEWED', 'VERIFIED', 'APPROVED', 'CORRECTED'):
                        logger.warning(f"Reprocessing Protection: Preserved reviewer-approved contribution: {existing_con.public_id}")
                        continue
                    else:
                        existing_con.delete()

                block_words = b["words"]
                vy_start = b["vy_start"]
                vy_end = b["vy_end"]
                
                # Separate words into columns based on visual vx coordinates
                date_words = [w for w in block_words if 20 <= w["vx0"] <= 85]
                name_addr_words = [w for w in block_words if 85 < w["vx0"] <= 330]
                code_words = [w for w in block_words if 330 < w["vx0"] <= 375]
                occ_emp_words = [w for w in block_words if 375 < w["vx0"] <= 540]
                amount_words = [w for w in block_words if 540 < w["vx0"] <= 630]
                cum_words = [w for w in block_words if 630 < w["vx0"] <= 792]
                
                # Group words in each column to visual lines
                date_lines = words_to_lines(date_words)
                name_addr_lines = words_to_lines(name_addr_words)
                occ_emp_lines = words_to_lines(occ_emp_words)
                amount_lines = words_to_lines(amount_words)
                cum_lines = words_to_lines(cum_words)
                
                # Checkbox detector
                orig_words = [w["original_tuple"] for w in block_words]
                contrib_code, code_conf = detect_checkbox_digital(
                    orig_words, vy_start, vy_end, rotation, page_width, page_height
                )
                
                # Parse Name, Address, and Intermediaries
                raw_name = ""
                raw_address = ""
                city, state, zip_code = "", "", ""
                inter_name = ""
                inter_address = ""
                
                contributor_lines = []
                intermediary_lines = []
                is_intermediary = False
                
                for line in name_addr_lines:
                    if "intermediary" in line.lower() or "received through" in line.lower():
                        is_intermediary = True
                        continue
                    if is_intermediary:
                        intermediary_lines.append(line)
                    else:
                        contributor_lines.append(line)
                        
                if contributor_lines:
                    raw_name = contributor_lines[0].strip()
                    if len(contributor_lines) > 1:
                        raw_address = " ".join(contributor_lines[1:]).strip()
                        # Extract city, state, zip from the last contributor line
                        last_line = contributor_lines[-1].strip()
                        addr_match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5})', last_line)
                        if addr_match:
                            city = addr_match.group(1).strip()
                            state = addr_match.group(2).strip()
                            zip_code = addr_match.group(3).strip()
                            
                if intermediary_lines:
                    inter_name = intermediary_lines[0].strip()
                    if len(intermediary_lines) > 1:
                        inter_address = " ".join(intermediary_lines[1:]).strip()
                        
                # Parse Occupation and Employer
                occupation = ""
                employer = ""
                if occ_emp_lines:
                    occupation = occ_emp_lines[0].strip()
                    if len(occ_emp_lines) > 1:
                        employer = " ".join(occ_emp_lines[1:]).strip()
                        
                # Parse Amounts
                raw_amount = amount_lines[0] if amount_lines else "0.00"
                amount_val = clean_amount(raw_amount)
                
                raw_cum = cum_lines[0] if cum_lines else "0.00"
                cum_val = clean_amount(raw_cum)
                
                # Extract election cycle from cumulative column (e.g. P2026)
                election_cycle = ""
                per_election_val = 0.0
                cycle_match = re.search(r'([P|G]\d{4})', raw_cum)
                if cycle_match:
                    election_cycle = cycle_match.group(1)
                    # Often the per-election total matches the cumulative or current amount
                    per_election_val = amount_val 
                    
                # Setup structured payload
                raw_block_text = " | ".join(words_to_lines(block_words))
                
                record = {
                    "filing_id": str(job.id),
                    "committee_name": filer_name,
                    "committee_id": committee_id,
                    "document_id": str(document.id),
                    "source_pdf_filename": document.original_filename,
                    "page_number": page.page_number,
                    "schedule_type": "A",
                    "visual_block_number": b["block_number"],
                    "date": b["date_text"],
                    "contributor_name": raw_name,
                    "contributor_normalized_proposed_name": raw_name,
                    "contributor_raw_address_text": raw_address,
                    "city": city,
                    "state": state,
                    "zip_code": zip_code,
                    "contributor_code": contrib_code,
                    "contributor_code_confidence": code_conf,
                    "occupation": occupation,
                    "employer": employer,
                    "amount": amount_val,
                    "cumulative_calendar_year_amount": cum_val,
                    "per_election_to_date_amount": per_election_val,
                    "election_cycle_notation": election_cycle,
                    "intermediary_name": inter_name,
                    "intermediary_address": inter_address,
                    "negative_or_refund": amount_val < 0,
                    "raw_block_text": raw_block_text
                }
                
                # Validate the record
                rating, field_confidences, warnings = validate_contribution_record(record)
                record["field_confidences"] = field_confidences
                record["block_confidence_rating"] = rating
                record["warnings"] = warnings
                
                # Write consolidated block to DB
                ExtractedField.objects.create(
                    extraction_job=job,
                    page=page,
                    field_type=f"contribution_block_{b['block_number']}",
                    raw_value=raw_block_text,
                    normalized_proposed_value=json.dumps(record),
                    confidence_score=field_confidences["name"],
                    reviewer_status=FieldReviewStatus.PROPOSED
                )
                
                # Automate cataloging and link contribution records
                try:
                    from apps.extraction.cataloger import catalog_contributor_block
                    catalog_contributor_block(record, page, import_batch=batch, session_cache=session_cache)
                except Exception as ex:
                    logger.error(f"Cataloger failed for block {b['block_number']}: {ex}", exc_info=True)
                
                # Write backward-compatible individual fields
                ExtractedField.objects.create(
                    extraction_job=job,
                    page=page,
                    field_type=f"block{b['block_number']}_name",
                    raw_value=raw_name,
                    normalized_proposed_value=raw_name,
                    confidence_score=field_confidences["name"],
                    reviewer_status=FieldReviewStatus.PROPOSED
                )
                ExtractedField.objects.create(
                    extraction_job=job,
                    page=page,
                    field_type=f"block{b['block_number']}_amount",
                    raw_value=str(amount_val),
                    normalized_proposed_value=str(amount_val),
                    confidence_score=field_confidences["amount"],
                    reviewer_status=FieldReviewStatus.PROPOSED
                )

        job.completed_at = timezone.now()
        job.status = 'COMPLETED'
        job.save()
        
    except Exception as e:
        job.status = 'FAILED'
        job.failure_reason = str(e)
        job.save()
        raise e
        
    return job

def calculate_entity_match_score(name_a, name_b):
    if not name_a or not name_b:
        return 0.0
    return SequenceMatcher(None, name_a.lower().strip(), name_b.lower().strip()).ratio() * 100.0
