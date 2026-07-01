import uuid
from django.db import models
from django.conf import settings

class SourceType(models.TextChoices):
    FORM_460 = 'FORM_460', 'Form 460 Campaign Disclosure'
    FORM_410 = 'FORM_410', 'Form 410 Statement of Organization'
    LOBBYING_DISCLOSURE = 'LOBBYING_DISCLOSURE', 'Lobbying Disclosure'
    MEETING_MINUTES = 'MEETING_MINUTES', 'Meeting Minutes'
    STAFF_REPORT = 'STAFF_REPORT', 'Staff Report'
    CONTRACT = 'CONTRACT', 'Government Contract'
    APPOINTMENT_RECORD = 'APPOINTMENT_RECORD', 'Appointment Record'
    PRA_RESPONSE = 'PRA_RESPONSE', 'Public Records Act Response'
    NEWS_ARTICLE = 'NEWS_ARTICLE', 'News Article / Investigative Report'
    OTHER = 'OTHER', 'Other Documented Source'

class ReliabilityClassification(models.TextChoices):
    OFFICIAL_PUBLIC_RECORD = 'OFFICIAL_PUBLIC_RECORD', 'Official Public Record'
    VERIFIED_PRIMARY = 'VERIFIED_PRIMARY', 'Verified Primary Source'
    CORROBORATED_SECONDARY = 'CORROBORATED_SECONDARY', 'Corroborated Secondary Source'
    UNVERIFIED_CLAIM = 'UNVERIFIED_CLAIM', 'Unverified Claim / Lead'

class PrivacyClassification(models.TextChoices):
    PUBLIC = 'PUBLIC', 'Public Record'
    INTERNAL = 'INTERNAL', 'Internal Research'
    RESTRICTED = 'RESTRICTED', 'Restricted / Sensitive'

class Source(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SourceType.choices, default=SourceType.OTHER)
    issuing_body = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=200, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    access_date = models.DateField(null=True, blank=True)
    original_url = models.URLField(max_length=500, blank=True)
    archive_url = models.URLField(max_length=500, blank=True)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    notes = models.TextField(blank=True)
    reliability = models.CharField(max_length=50, choices=ReliabilityClassification.choices, default=ReliabilityClassification.OFFICIAL_PUBLIC_RECORD)
    privacy_classification = models.CharField(max_length=50, choices=PrivacyClassification.choices, default=PrivacyClassification.PUBLIC)
    filing_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.public_id} - {self.title}"

class SourceLocator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='locators')
    document = models.ForeignKey('documents.Document', on_delete=models.SET_NULL, null=True, blank=True, related_name='locators')
    page = models.ForeignKey('documents.DocumentPage', on_delete=models.SET_NULL, null=True, blank=True, related_name='locators')
    page_range = models.CharField(max_length=50, blank=True)
    bounding_box_json = models.JSONField(null=True, blank=True, help_text="[vx0, vy0, vx1, vy1]")
    section = models.CharField(max_length=100, blank=True)
    table_identifier = models.CharField(max_length=100, blank=True)
    agenda_item = models.CharField(max_length=50, blank=True)
    filing_schedule = models.CharField(max_length=50, blank=True)
    locator_description = models.TextField(blank=True)

    def __str__(self):
        page_num = self.page.page_number if self.page else "N/A"
        return f"Locator for {self.source.public_id} - Page {page_num}"
