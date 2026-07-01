import uuid
from django.db import models
from django.conf import settings
from apps.documents.models import Document, DocumentPage
from apps.entities.models import Entity

class FieldReviewStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', 'Proposed / Machine Extracted'
    APPROVED = 'APPROVED', 'Approved by Reviewer'
    CORRECTED = 'CORRECTED', 'Corrected by Reviewer'
    REJECTED = 'REJECTED', 'Rejected'
    ILLEGIBLE = 'ILLEGIBLE', 'Illegible Field'

class ExtractionJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='extraction_jobs')
    job_type = models.CharField(max_length=50, default='FORM_460_PARSER')
    processing_engine = models.CharField(max_length=100, default='PyMuPDF+Regex')
    engine_version = models.CharField(max_length=50, default='1.0')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, default='COMPLETED')
    logs = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.job_type} on {self.document.original_filename}"

class ExtractedField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    extraction_job = models.ForeignKey(ExtractionJob, on_delete=models.CASCADE, related_name='extracted_fields')
    page = models.ForeignKey(DocumentPage, on_delete=models.SET_NULL, null=True, blank=True, related_name='fields')
    
    field_type = models.CharField(max_length=100, help_text="e.g., committee_name, donor_name, contribution_amount")
    raw_value = models.TextField(blank=True)
    normalized_proposed_value = models.TextField(blank=True)
    bounding_box_json = models.JSONField(null=True, blank=True, help_text="[x0, y0, x1, y1]")
    confidence_score = models.FloatField(default=100.0)
    
    reviewer_status = models.CharField(max_length=30, choices=FieldReviewStatus.choices, default=FieldReviewStatus.PROPOSED)
    reviewer_correction = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    linked_canonical_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_extracted_fields')

    def __str__(self):
        return f"{self.field_type}: {self.raw_value} ({self.reviewer_status})"

class ExtractedContributorBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(DocumentPage, on_delete=models.CASCADE, related_name='contributor_blocks')
    block_number = models.IntegerField()
    raw_text = models.TextField()
    bounding_box_json = models.JSONField(null=True, blank=True, help_text="[vx0, vy0, vx1, vy1]")
    extraction_method = models.CharField(max_length=50, default='embedded_text_layout') # embedded_text_layout or OCR_layout
    parser_version = models.CharField(max_length=50, default='2.0')
    original_parsed_json = models.JSONField(default=dict)

    def __str__(self):
        return f"Block {self.block_number} on Page {self.page.page_number} ({self.extraction_method})"

class EntityMatchAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contribution = models.ForeignKey('transactions.Contribution', on_delete=models.CASCADE, related_name='match_attempts')
    selected_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='match_attempts')
    match_method = models.CharField(max_length=50) # e.g. EXACT_COMMITTEE_ID, EXACT_NORMALIZED_NAME, etc.
    match_score = models.FloatField(default=0.0)
    name_score = models.FloatField(default=0.0)
    location_score = models.FloatField(default=0.0)
    employer_score = models.FloatField(default=0.0)
    entity_type_compatibility = models.BooleanField(default=True)
    committee_id_match = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    model_version = models.CharField(max_length=50, default='2.0')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"MatchAttempt ({self.match_method}) -> {self.selected_entity.public_id} ({self.match_score}%)"

class EntityMatchCandidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match_attempt = models.ForeignKey(EntityMatchAttempt, on_delete=models.CASCADE, related_name='candidates')
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    match_method = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Candidate {self.entity.public_id} (Score: {self.score}%)"
