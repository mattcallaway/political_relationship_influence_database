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
    
    public_id = models.CharField(max_length=20, unique=True, db_index=True, null=True, blank=True)
    document_type = models.CharField(max_length=50, blank=True)
    processing_version = models.CharField(max_length=10, default='1.0')
    publication_classification = models.CharField(max_length=50, default='PUBLIC')

    def save(self, *args, **kwargs):
        if not self.public_id:
            count = Document.objects.count()
            for attempt in range(1, 100):
                candidate = f"DOC{count + attempt:06d}"
                if not Document.objects.filter(public_id=candidate).exists():
                    self.public_id = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.original_filename} ({self.sha256_hash[:8]})"

class DocumentPage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='pages')
    page_number = models.IntegerField()
    extracted_text = models.TextField(blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True, help_text="Average OCR confidence score 0-100")
    page_image = models.ImageField(upload_to='page_images/%Y/%m/', null=True, blank=True)
    processing_status = models.CharField(max_length=30, default='EXTRACTED')
    
    ocr_text = models.TextField(blank=True)
    page_width = models.FloatField(null=True, blank=True)
    page_height = models.FloatField(null=True, blank=True)
    review_status = models.CharField(max_length=30, default='UNREVIEWED')

    class Meta:
        unique_together = ('document', 'page_number')
        ordering = ['page_number']

    def __str__(self):
        return f"{self.document.original_filename} - Page {self.page_number}"
