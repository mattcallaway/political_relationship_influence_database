import pytest
from django.test import Client
from apps.audit.models import ImportBatch
from apps.entities.models import Entity
from apps.transactions.models import Contribution, Expenditure, ReviewStatus
from apps.transactions.reconciliation import reconcile_amendment_batches

@pytest.mark.django_db
def test_reconciliation_contributions_and_expenditures():
    # 1. Setup entities
    committee = Entity.objects.create(public_id="RECON_FILER", canonical_name="Recon Committee", entity_type="COMMITTEE")
    donor = Entity.objects.create(public_id="RECON_DONOR", canonical_name="Recon Donor Corp", entity_type="ORGANIZATION")
    payee = Entity.objects.create(public_id="RECON_PAYEE", canonical_name="Recon Vendor LLC", entity_type="ORGANIZATION")
    
    # 2. Setup batches
    batch_old = ImportBatch.objects.create(batch_name="Original Import", status="COMPLETED")
    batch_new = ImportBatch.objects.create(batch_name="Amended Import", status="COMPLETED")
    
    # 3. Create original transactions
    con_old = Contribution.objects.create(
        public_id="CON_OLD_1",
        filer_committee=committee,
        donor_entity=donor,
        donor_raw_name="Recon Donor Corp",
        amount=1000.0,
        import_batch=batch_old,
        review_status=ReviewStatus.AUTO_IMPORTED
    )
    
    exp_old = Expenditure.objects.create(
        public_id="EXP_OLD_1",
        filer_committee=committee,
        payee_entity=payee,
        payee_raw_name="Recon Vendor LLC",
        amount=500.0,
        import_batch=batch_old,
        review_status=ReviewStatus.AUTO_IMPORTED
    )
    
    # 4. Create amended transactions
    con_new = Contribution.objects.create(
        public_id="CON_NEW_1",
        filer_committee=committee,
        donor_entity=donor,
        donor_raw_name="Recon Donor Corp",
        amount=1000.0, # matches
        import_batch=batch_new,
        review_status=ReviewStatus.AUTO_IMPORTED
    )
    
    exp_new = Expenditure.objects.create(
        public_id="EXP_NEW_1",
        filer_committee=committee,
        payee_entity=payee,
        payee_raw_name="Recon Vendor LLC",
        amount=500.0, # matches
        import_batch=batch_new,
        review_status=ReviewStatus.AUTO_IMPORTED
    )
    
    # 5. Run reconciliation
    success = reconcile_amendment_batches(batch_old, batch_new)
    assert success
    
    # 6. Verify statuses and foreign keys
    con_old.refresh_from_db()
    con_new.refresh_from_db()
    exp_old.refresh_from_db()
    exp_new.refresh_from_db()
    
    assert con_old.amendment_status == 'SUPERSEDED'
    assert con_old.superseded_by == con_new
    assert con_new.amendment_status == 'AMENDED'
    
    assert exp_old.amendment_status == 'SUPERSEDED'
    assert exp_old.superseded_by == exp_new
    assert exp_new.amendment_status == 'AMENDED'
    
    # 7. Check trigger view POST
    client = Client()
    post_response = client.post('/transactions/reconcile/', {
        'old_batch_id': str(batch_old.id),
        'new_batch_id': str(batch_new.id)
    })
    assert post_response.status_code == 302
