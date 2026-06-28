import uuid
from django.db import models
from django.conf import settings

class EntityType(models.TextChoices):
    PERSON = 'PERSON', 'Person'
    ORGANIZATION = 'ORGANIZATION', 'Organization'

class EntityStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', 'Proposed / In Intake'
    APPROVED = 'APPROVED', 'Approved Canonical Entity'
    MERGED = 'MERGED', 'Merged into another entity'
    REJECTED = 'REJECTED', 'Rejected'

class PublicationStatus(models.TextChoices):
    INTERNAL_ONLY = 'INTERNAL_ONLY', 'Internal Only'
    NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Review'
    PUBLISHABLE = 'PUBLISHABLE', 'Publishable'
    PUBLISHED = 'PUBLISHED', 'Published'
    WITHHELD = 'WITHHELD', 'Withheld'

class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    canonical_name = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=EntityStatus.choices, default=EntityStatus.APPROVED)
    publication_status = models.CharField(max_length=20, choices=PublicationStatus.choices, default=PublicationStatus.INTERNAL_ONLY)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_entities')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_entities')

    class Meta:
        verbose_name_plural = "Entities"

    def __str__(self):
        return f"{self.public_id} - {self.canonical_name}"

class Person(models.Model):
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, primary_key=True, related_name='person_profile')
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=20, blank=True)
    display_name = models.CharField(max_length=255)
    occupation = models.CharField(max_length=200, blank=True)
    public_role = models.CharField(max_length=200, blank=True)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.display_name

class OrganizationCategory(models.TextChoices):
    CAMPAIGN_COMMITTEE = 'CAMPAIGN_COMMITTEE', 'Campaign Committee'
    DEVELOPER_CORP = 'DEVELOPER_CORP', 'Development Corporation'
    GOVT_AGENCY = 'GOVT_AGENCY', 'Government Agency'
    LOBBYING_FIRM = 'LOBBYING_FIRM', 'Lobbying / Public Affairs Firm'
    NON_PROFIT = 'NON_PROFIT', 'Non-Profit / Advocacy Group'
    OTHER = 'OTHER', 'Other Organization'

class Organization(models.Model):
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, primary_key=True, related_name='organization_profile')
    org_category = models.CharField(max_length=50, choices=OrganizationCategory.choices, default=OrganizationCategory.OTHER)
    legal_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255, blank=True)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    formation_date = models.DateField(null=True, blank=True)
    dissolution_date = models.DateField(null=True, blank=True)
    committee_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="State FPPC or FEC ID")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.legal_name

class Alias(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='aliases')
    alias_text = models.CharField(max_length=255, db_index=True)
    alias_type = models.CharField(max_length=50, default='ALT_NAME')
    normalized_alias = models.CharField(max_length=255, db_index=True)
    effective_start = models.DateField(null=True, blank=True)
    effective_end = models.DateField(null=True, blank=True)
    review_status = models.CharField(max_length=20, default='APPROVED')

    def __str__(self):
        return f"{self.alias_text} -> {self.entity.canonical_name}"
