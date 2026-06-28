import uuid
from django.db import models
from apps.entities.models import Entity
from apps.sources.models import Source
from apps.documents.models import DocumentPage

class ReviewStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', 'Proposed / Machine Extracted'
    APPROVED = 'APPROVED', 'Approved by Reviewer'
    CORRECTED = 'CORRECTED', 'Corrected by Reviewer'
    REJECTED = 'REJECTED', 'Rejected'

class Contribution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    filer_committee = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='contributions_received')
    donor_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='contributions_made')
    donor_raw_name = models.CharField(max_length=255)
    
    transaction_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cumulative_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    schedule = models.CharField(max_length=50, default='Schedule A')
    transaction_code = models.CharField(max_length=50, blank=True, help_text="IND, COM, OTH, PTY, SCC")
    
    occupation = models.CharField(max_length=200, blank=True)
    employer = models.CharField(max_length=200, blank=True)
    city_state_zip = models.CharField(max_length=200, blank=True)
    
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    document_page = models.ForeignKey(DocumentPage, on_delete=models.SET_NULL, null=True, blank=True)
    source_locator = models.CharField(max_length=100, blank=True)
    review_status = models.CharField(max_length=30, choices=ReviewStatus.choices, default=ReviewStatus.PROPOSED)

    def __str__(self):
        return f"{self.public_id}: ${self.amount} from {self.donor_raw_name}"

class Expenditure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    
    filer_committee = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='expenditures_made')
    payee_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenditures_received')
    payee_raw_name = models.CharField(max_length=255)
    
    transaction_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    schedule = models.CharField(max_length=50, default='Schedule E')
    transaction_code = models.CharField(max_length=50, blank=True, help_text="CMP, CNS, LIT, POS, PRO, PRT, RAD, SAL, TEL, TRV, VOT, WEB")
    
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    document_page = models.ForeignKey(DocumentPage, on_delete=models.SET_NULL, null=True, blank=True)
    review_status = models.CharField(max_length=30, choices=ReviewStatus.choices, default=ReviewStatus.PROPOSED)

    def __str__(self):
        return f"{self.public_id}: ${self.amount} to {self.payee_raw_name}"

class Loan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    lender_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_given')
    borrower_committee = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='loans_received')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.FloatField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    agency_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='agency_contracts')
    vendor_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='vendor_contracts')
    contract_title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    execution_date = models.DateField(null=True, blank=True)
    scope = models.TextField(blank=True)

class LobbyingActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_id = models.CharField(max_length=20, unique=True, db_index=True)
    lobbyist_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='lobbying_as_firm')
    client_entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='lobbying_as_client')
    agency_entity = models.ForeignKey(Entity, on_delete=models.SET_NULL, null=True, blank=True, related_name='lobbying_targeted_agency')
    reporting_period = models.CharField(max_length=50, blank=True)
    compensation_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    matters_described = models.TextField(blank=True)
