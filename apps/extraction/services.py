import re
from difflib import SequenceMatcher
from apps.extraction.models import ExtractionJob, ExtractedField, FieldReviewStatus
from apps.entities.models import Entity

def parse_form_460(document):
    job = ExtractionJob.objects.create(
        document=document,
        job_type='FORM_460_PARSER',
        processing_engine='Regex+PyMuPDF',
        status='COMPLETED'
    )

    for page in document.pages.all():
        text = page.extracted_text
        if not text:
            continue

        # Extract Committee Name / Filer
        committee_match = re.search(r'(?:NAME OF FILER|Filer Name)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if committee_match:
            ExtractedField.objects.create(
                extraction_job=job,
                page=page,
                field_type='committee_name',
                raw_value=committee_match.group(1).strip(),
                normalized_proposed_value=committee_match.group(1).strip(),
                confidence_score=95.0,
                reviewer_status=FieldReviewStatus.PROPOSED
            )

        # Extract Schedule A Contributions (e.g. $2,500.00 from John Doe)
        contrib_matches = re.findall(r'([A-Z\s,]+)\s+\$?([0-9,]+\.[0-9]{2})', text)
        for name, amount in contrib_matches[:5]:
            if len(name.strip()) > 3:
                ExtractedField.objects.create(
                    extraction_job=job,
                    page=page,
                    field_type='contribution_row',
                    raw_value=f"{name.strip()} - ${amount}",
                    normalized_proposed_value=name.strip(),
                    confidence_score=88.0,
                    reviewer_status=FieldReviewStatus.PROPOSED
                )

    return job

def calculate_entity_match_score(name_a, name_b):
    if not name_a or not name_b:
        return 0.0
    return SequenceMatcher(None, name_a.lower().strip(), name_b.lower().strip()).ratio() * 100.0
