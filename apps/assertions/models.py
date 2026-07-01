import uuid
from django.db import models
from django.conf import settings
from apps.entities.models import Entity, PublicationStatus
from apps.sources.models import Source
from apps.documents.models import DocumentPage

class ClaimType(models.TextChoices):
    FACTUAL = 'FACTUAL', 'Factual Assertion'
    INTERPRETIVE = 'INTERPRETIVE', 'Analytic Interpretation'
    ALLEGATION = 'ALLEGATION', 'Allegation'
    HYPOTHESIS = 'HYPOTHESIS', 'Research Hypothesis'
    CONTEXT = 'CONTEXT', 'Historical Context'

class VerificationStatus(models.TextChoices):
    LEAD = 'LEAD', 'Lead / Unverified'
    UNVERIFIED = 'UNVERIFIED', 'Unverified'
    PARTIALLY_VERIFIED = 'PARTIALLY_VERIFIED', 'Partially Verified'
    VERIFIED = 'VERIFIED', 'Verified'
    DISPUTED = 'DISPUTED', 'Disputed'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'
    RETRACTED = 'RETRACTED', 'Retracted'
    ARCHIVED = 'ARCHIVED', 'Archived'

class PredicateVocabulary(models.Model):
    predicate_code = models.CharField(max_length=100, primary_key=True)
    label = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    direction = models.CharField(max_length=50, default='Directed')
    definition = models.TextField(blank=True)
    inverse_predicate = models.CharField(max_length=100, blank=True)
    requires_object_entity = models.BooleanField(default=True)
    allows_object_value = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    sensitive_claim = models.BooleanField(default=False)
    auto_generatable = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    domain_entity_type = models.CharField(max_length=50, blank=True)
    range_entity_type = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.predicate_code} ({self.label})"

class SupportType(models.TextChoices):
    PRIMARY = 'PRIMARY', 'Primary Direct Support'
    CORROBORATING = 'CORROBORATING', 'Corroborating Support'
    CONTRADICTING = 'CONTRADICTING', 'Contradicting Evidence'
    CONTEXTUAL = 'CONTEXTUAL', 'Contextual Background'

class Assertion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    subject_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='subject_assertions')
    predicate = models.CharField(max_length=100, db_index=True, help_text="e.g., principal_of, contributed_to, employee_of")
    object_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='object_assertions')
    object_value = models.CharField(max_length=255, blank=True, help_text="Literal value if object is not an entity")
    
    claim_type = models.CharField(max_length=30, choices=ClaimType.choices, default=ClaimType.FACTUAL)
    verification_status = models.CharField(max_length=30, choices=VerificationStatus.choices, default=VerificationStatus.UNVERIFIED)
    confidence_score = models.FloatField(default=100.0)
    
    effective_start = models.DateField(null=True, blank=True)
    effective_end = models.DateField(null=True, blank=True)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    sensitive_claim = models.BooleanField(default=False)
    publication_status = models.CharField(max_length=30, choices=PublicationStatus.choices, default=PublicationStatus.INTERNAL_ONLY)
    explanatory_note = models.TextField(blank=True)
    
    interpretation_required = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assertions')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assertions_reviewed_legacy')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assertions')
    review_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        obj_str = self.object_entity.canonical_name if self.object_entity else self.object_value
        return f"{self.public_id}: {self.subject_entity.canonical_name} [{self.predicate}] {obj_str}"

class AssertionSource(models.Model):
    assertion = models.ForeignKey(Assertion, on_delete=models.CASCADE, related_name='evidence_sources')
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='assertions_supported')
    support_type = models.CharField(max_length=30, choices=SupportType.choices, default=SupportType.PRIMARY)
    document_page = models.ForeignKey(DocumentPage, on_delete=models.SET_NULL, null=True, blank=True)
    locator_text = models.CharField(max_length=255, blank=True, help_text="Page number, paragraph, or section reference")
    concise_evidence_note = models.TextField(blank=True)
    
    source_locator = models.ForeignKey('sources.SourceLocator', on_delete=models.CASCADE, null=True, blank=True, related_name='assertion_sources')
    evidence_note = models.TextField(blank=True)
    source_quality = models.CharField(max_length=50, blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assertion_sources_reviewed')

    def __str__(self):
        return f"Evidence for {self.assertion.public_id} in {self.source.public_id}"
