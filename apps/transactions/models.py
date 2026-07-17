import uuid
from django.db import models
from django.conf import settings
from apps.entities.models import Entity
from apps.sources.models import Source
from apps.documents.models import DocumentPage

class ReviewStatus(models.TextChoices):
    AUTO_IMPORTED = 'AUTO_IMPORTED', 'Auto Imported'
    AUTO_MATCHED = 'AUTO_MATCHED', 'Auto Matched'
    NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Review'
    REVIEWED = 'REVIEWED', 'Reviewed'
    VERIFIED = 'VERIFIED', 'Verified'
    SUPERSEDED = 'SUPERSEDED', 'Superseded'
    REJECTED = 'REJECTED', 'Rejected'
    PROPOSED = 'PROPOSED', 'Proposed / Machine Extracted'
    APPROVED = 'APPROVED', 'Approved by Reviewer'
    CORRECTED = 'CORRECTED', 'Corrected by Reviewer'

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
    review_status = models.CharField(max_length=30, choices=ReviewStatus.choices, default=ReviewStatus.AUTO_IMPORTED)
    amendment_status = models.CharField(max_length=50, default='ORIGINAL')
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    document = models.ForeignKey('documents.Document', on_delete=models.CASCADE, null=True, blank=True, related_name='contributions')
    extracted_block = models.ForeignKey('extraction.ExtractedContributorBlock', on_delete=models.SET_NULL, null=True, blank=True, related_name='contributions')
    import_batch = models.ForeignKey('audit.ImportBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='contributions')
    match_attempt = models.ForeignKey('extraction.EntityMatchAttempt', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_contributions')

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
    
    # Milestone 1 attributes extension
    candidate_measure = models.CharField(max_length=255, blank=True, help_text="Supported or opposed candidate/measure")
    agent_contractor = models.CharField(max_length=255, blank=True)
    subcontractor = models.CharField(max_length=255, blank=True)
    campaign = models.ForeignKey('campaigns.Campaign', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenditures')
    consultant_vendor_role = models.CharField(max_length=100, blank=True, help_text="e.g. CONSULTANT_TO, VENDOR_TO")
    source_page = models.IntegerField(null=True, blank=True)
    is_independent_expenditure = models.BooleanField(default=False)
    support_oppose = models.CharField(max_length=10, blank=True, choices=[('SUPPORT', 'Support'), ('OPPOSE', 'Oppose')])
    filing_id = models.CharField(max_length=100, blank=True)
    filing_period = models.CharField(max_length=100, blank=True)
    source_locator = models.CharField(max_length=100, blank=True)
    extraction_status = models.CharField(max_length=50, default='SUCCESS')
    amendment_status = models.CharField(max_length=50, default='ORIGINAL')
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    import_batch = models.ForeignKey('audit.ImportBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenditures')
    raw_extraction_data = models.TextField(blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_expenditures')

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

class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100) # e.g. MATCH_CONFIRMED, MATCH_OVERRIDDEN, MERGE, REPROCESSING
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    prior_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"AuditEvent {self.action} on {self.table_name}:{self.record_id} at {self.timestamp}"
