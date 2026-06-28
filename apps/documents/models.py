import uuid
from django.db import models
from django.conf import settings
from apps.sources.models import Source

class DocumentProcessingStatus(models.TextChoices):
    UPLOADED = 'UPLOADED', 'Uploaded'
    HASHING = 'HASHING', 'Hashing'
    QUEUED = 'QUEUED', 'Queued for Extraction'
    EXTRACTING = 'EXTRACTING', 'Extracting Text'
    OCR_COMPLETE = 'OCR_COMPLETE', 'OCR Complete'
    EXTRACTION_COMPLETE = 'EXTRACTION_COMPLETE', 'Extraction Complete'
    NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Review'
    REVIEWED = 'REVIEWED', 'Reviewed'
    FAILED = 'FAILED', 'Processing Failed'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='documents/%Y/%m/')
    media_type = models.CharField(max_length=100, default='application/pdf')
    byte_size = models.BigIntegerField(default=0)
    sha256_hash = models.CharField(max_length=64, unique=True, db_index=True)
    
    upload_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    page_count = models.IntegerField(default=0)
    
    has_native_text = models.BooleanField(default=False)
    ocr_applied = models.BooleanField(default=False)
    ocr_provider = models.CharField(max_length=50, blank=True, default='Tesseract')
    ocr_version = models.CharField(max_length=50, blank=True)
    
    processing_status = models.CharField(max_length=30, choices=DocumentProcessingStatus.choices, default=DocumentProcessingStatus.UPLOADED)
    original_preserved = models.BooleanField(default=True, editable=False)

    def __str__(self):
        return f"{self.original_filename} ({self.sha256_hash[:8]})"

class DocumentPage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()
    extracted_text = models.TextField(blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True, help_text="Average OCR confidence score 0-100")
    page_image = models.ImageField(upload_to='page_images/%Y/%m/', null=True, blank=True)
    processing_status = models.CharField(max_length=30, default='EXTRACTED')

    class Meta:
        unique_together = ('document', 'page_number')
        ordering = ['page_number']

    def __str__(self):
        return f"{self.document.original_filename} - Page {self.page_number}"
