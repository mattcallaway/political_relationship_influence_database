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
