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

class Meeting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    government_body = models.ForeignKey(GovernmentBody, on_delete=models.CASCADE, related_name='meetings')
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    agenda_source = models.ForeignKey('sources.Source', on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings_agendized')
    minutes_source = models.ForeignKey('sources.Source', on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings_minuted')

    def __str__(self):
        return f"Meeting of {self.government_body.body_name} on {self.date}"

class AgendaItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='agenda_items')
    item_number = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    related_project = models.ForeignKey('entities.Entity', on_delete=models.SET_NULL, null=True, blank=True, related_name='agenda_items')
    staff_recommendation = models.CharField(max_length=255, blank=True)
    outcome = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.meeting} - Item {self.item_number}: {self.title[:50]}"

class Motion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agenda_item = models.ForeignKey(AgendaItem, on_delete=models.CASCADE, related_name='motions')
    motion_text = models.TextField()
    mover = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='motions_moved')
    seconder = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='motions_seconded')
    result = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Motion on {self.agenda_item.item_number}: {self.result}"
