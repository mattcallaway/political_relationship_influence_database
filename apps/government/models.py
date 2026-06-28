import uuid
from django.db import models
from apps.entities.models import Entity

class PublicOffice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    office_name = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')
    term_length_years = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.office_name} ({self.jurisdiction})"

class GovernmentBody(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    entity = models.OneToOneField(Entity, on_delete=models.CASCADE, related_name='body_profile', null=True, blank=True)
    body_name = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=100, default='Sonoma County')

    def __str__(self):
        return self.body_name

class VoteResult(models.TextChoices):
    AYE = 'AYE', 'Aye / Yes'
    NO = 'NO', 'No'
    ABSTAIN = 'ABSTAIN', 'Abstain'
    RECUSED = 'RECUSED', 'Recused'
    ABSENT = 'ABSENT', 'Absent'

class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    voter_person = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='votes_cast')
    governing_body = models.ForeignKey(GovernmentBody, on_delete=models.CASCADE, related_name='votes_taken')
    meeting_date = models.DateField()
    agenda_item = models.CharField(max_length=100)
    item_title = models.CharField(max_length=255)
    vote_cast = models.CharField(max_length=20, choices=VoteResult.choices)
    outcome = models.CharField(max_length=100, blank=True, help_text="e.g. Motion Passed 4-1")

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    person_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='appointments')
    body_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='body_appointments')
    appointer_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='made_appointments')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    position_title = models.CharField(max_length=200, blank=True)

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    event_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, default='HEARING')
    event_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
