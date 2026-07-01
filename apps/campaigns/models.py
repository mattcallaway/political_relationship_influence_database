import uuid
from django.db import models
from apps.entities.models import Entity

class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, related_name='campaign_profile', null=True, blank=True)
    campaign_name = models.CharField(max_length=255)
    election_year = models.IntegerField()
    office_sought = models.CharField(max_length=200, blank=True)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    outcome = models.CharField(max_length=50, blank=True)
    
    candidate = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='campaigns_as_candidate', null=True, blank=True)
    office = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='campaigns_for_office', null=True, blank=True)
    election_date = models.DateField(null=True, blank=True)
    election_cycle = models.CharField(max_length=50, blank=True)
    committee = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns_funded')
    campaign_status = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.public_id} - {self.campaign_name} ({self.election_year})"

class Committee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, related_name='committee_profile', null=True, blank=True)
    fppc_id = models.CharField(max_length=50, blank=True, db_index=True, help_text="California FPPC ID number")
    committee_name = models.CharField(max_length=255)
    treasurer_name = models.CharField(max_length=200, blank=True)
    candidate_or_measure = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    committee_type = models.CharField(max_length=100, blank=True)
    controlling_candidate = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='committees_controlled')
    sponsor = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='committees_sponsored')

    def __str__(self):
        return f"{self.public_id} - {self.committee_name} (FPPC: {self.fppc_id})"

class BallotMeasure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    measure_letter = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    election_date = models.DateField()
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    summary = models.TextField(blank=True)
    passed = models.BooleanField(null=True, blank=True)
    
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, related_name='ballot_measure_profile', null=True, blank=True)
    measure_number = models.CharField(max_length=20, blank=True)
    result = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Measure {self.measure_letter} ({self.election_date.year}) - {self.title}"
