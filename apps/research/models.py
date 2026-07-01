import uuid
from django.db import models
from django.conf import settings
from apps.entities.models import Entity

class IntakeItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    title_description = models.CharField(max_length=255)
    url_or_file = models.CharField(max_length=500, blank=True)
    item_type = models.CharField(max_length=50, default='LEAD')
    submitted_by = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=20, default='MEDIUM')
    processing_status = models.CharField(max_length=30, default='NEW')
    notes = models.TextField(blank=True)

class ResearchTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    task_title = models.CharField(max_length=255)
    assigned_researcher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, default='MEDIUM')
    status = models.CharField(max_length=30, default='OPEN')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    collection = models.ForeignKey('ResearchCollection', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')

class OpenQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    related_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, default='OPEN')
    collection = models.ForeignKey('ResearchCollection', on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')

class PRARequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    target_agency = models.CharField(max_length=200)
    request_summary = models.TextField()
    submission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='DRAFT')
    tracking_number = models.CharField(max_length=100, blank=True)
    collection = models.ForeignKey('ResearchCollection', on_delete=models.SET_NULL, null=True, blank=True, related_name='pra_requests')

class EntityMatchCandidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_1 = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='match_candidates_as_1')
    entity_2 = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='match_candidates_as_2')
    match_score = models.FloatField(help_text="Fuzzy similarity score 0-100")
    matching_fields = models.JSONField(default=list)
    conflicting_fields = models.JSONField(default=list)
    status = models.CharField(max_length=30, default='PENDING')

class DuplicateReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='duplicate_reviews')
    merged_into = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='absorbed_entities')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=50)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DataQualityIssue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_type = models.CharField(max_length=100)
    description = models.TextField()
    affected_object_type = models.CharField(max_length=100)
    affected_object_id = models.CharField(max_length=100)
    is_resolved = models.BooleanField(default=False)

class ResearchLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    repository = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    research_use = models.TextField(blank=True)
    priority = models.CharField(max_length=20, default='MEDIUM')
    access_notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, default='ACTIVE')

class ResearchCollection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    entities = models.ManyToManyField('entities.Entity', blank=True, related_name='research_collections')
    sources = models.ManyToManyField('sources.Source', blank=True, related_name='research_collections')
    contributions = models.ManyToManyField('transactions.Contribution', blank=True, related_name='research_collections')
    assertions = models.ManyToManyField('assertions.Assertion', blank=True, related_name='research_collections')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='research_collections')

    def __str__(self):
        return self.name

class SavedSearch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    query_string = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.query_string})"
