import uuid
from django.db import models
from django.conf import settings

class ChangeLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    table_name = models.CharField(max_length=100, db_index=True)
    record_id = models.CharField(max_length=100, db_index=True)
    change_type = models.CharField(max_length=50)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    prior_value_summary = models.TextField(blank=True, null=True)
    new_value_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Change {self.change_type} on {self.table_name}:{self.record_id}"

class ReviewDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_model = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    decision = models.CharField(max_length=50)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ControlledVocabularyValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=200)
    definition = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    deprecated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('category', 'code')

    def __str__(self):
        return f"{self.category}:{self.code}"

class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_name = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_dry_run = models.BooleanField(default=False)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, default='IN_PROGRESS')
    summary_counts = models.JSONField(default=dict)

    def __str__(self):
        return f"ImportBatch {self.batch_name} ({self.status})"

class ImportRow(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name='rows')
    source_sheet = models.CharField(max_length=100)
    source_row_index = models.IntegerField()
    raw_data = models.JSONField()
    status = models.CharField(max_length=50, default='IMPORTED')
    error_message = models.TextField(blank=True)

class LegacyIdentifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_id = models.CharField(max_length=100, unique=True, db_index=True)
    current_public_id = models.CharField(max_length=100, db_index=True)
    target_model = models.CharField(max_length=100)
    migration_notes = models.TextField(blank=True)
    
    entity = models.ForeignKey('entities.Entity', on_delete=models.SET_NULL, null=True, blank=True, related_name='legacy_identifiers')
    originating_system = models.CharField(max_length=100, blank=True)
    source_workbook = models.CharField(max_length=255, blank=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='legacy_identifiers')

    def __str__(self):
        return f"{self.legacy_id} -> {self.current_public_id or self.entity.public_id} ({self.target_model})"
