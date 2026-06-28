import uuid
from django.db import models
from apps.entities.models import Entity

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    project_name = models.CharField(max_length=255)
    applicant_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_projects')
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    status = models.CharField(max_length=50, default='PROPOSED')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.public_id} - {self.project_name}"

class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='properties')
    apn = models.CharField(max_length=50, blank=True, help_text="Assessor's Parcel Number")
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, default='Santa Rosa')
