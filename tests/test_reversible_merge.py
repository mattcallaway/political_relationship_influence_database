import pytest
from django.test import Client
from apps.entities.models import Entity, EntityStatus, EntityMerge, Alias
from apps.transactions.models import Contribution, Expenditure
from apps.government.models import Appointment, Vote, GovernmentBody

@pytest.mark.django_db
def test_comprehensive_reversible_entity_merge():
    client = Client()
    
    # 1. Create source and target entities
    source = Entity.objects.create(
        public_id='ENT_SRC_1',
        canonical_name='Source Candidate',
        entity_type='PERSON',
        status=EntityStatus.PROVISIONAL_AUTO_CREATED
    )
    target = Entity.objects.create(
        public_id='ENT_TGT_1',
        canonical_name='Target Candidate',
        entity_type='PERSON',
        status=EntityStatus.VERIFIED
    )
    
    # Recipient entity
    recipient = Entity.objects.create(
        public_id='ENT_REC_1',
        canonical_name='Recip Committee',
        entity_type='COMMITTEE'
    )
    
    # 2. Add some relations pointing to source
    con = Contribution.objects.create(
        public_id='CON_MERGE_1',
        filer_committee=recipient,
        donor_entity=source,
        donor_raw_name='Source Candidate',
        amount=500.00,
        transaction_date='2026-07-01'
    )
    
    gov_body = GovernmentBody.objects.create(
        public_id='GOV_BODY_1',
        body_name='Sonoma Supervisors'
    )
    
    vote = Vote.objects.create(
        voter_person=source,
        governing_body=gov_body,
        meeting_date='2026-07-01',
        agenda_item='Item 1',
        item_title='Rezoning approval',
        vote_cast='AYE'
    )
    
    # Verify initial pointers
    assert con.donor_entity == source
    assert vote.voter_person == source
    
    # 3. Post the merge request
    response = client.post(f'/extraction/merge/{source.id}/', {
        'target_entity': str(target.id),
        'reason': 'Duplicate candidates identified'
    })
    assert response.status_code == 302
    
    # Reload and assert status changes
    source.refresh_from_db()
    assert source.status == EntityStatus.MERGED
    
    con.refresh_from_db()
    vote.refresh_from_db()
    # Relations reassigned to target!
    assert con.donor_entity == target
    assert vote.voter_person == target
    
    # Verify Alias created on target
    assert Alias.objects.filter(entity=target, alias_text=source.canonical_name).exists()
    
    # Verify EntityMerge details
    merge_rec = EntityMerge.objects.filter(source_entity=source, target_entity=target).first()
    assert merge_rec is not None
    assert merge_rec.is_reversed is False
    assert merge_rec.reassigned_relations != {}
    
    # 4. Reverse the merge
    rev_response = client.post(f'/extraction/merge/reverse/{merge_rec.id}/')
    assert rev_response.status_code == 302
    
    # Reload and verify restore
    source.refresh_from_db()
    assert source.status == EntityStatus.PROVISIONAL_AUTO_CREATED
    
    con.refresh_from_db()
    vote.refresh_from_db()
    # Relations restored back to source!
    assert con.donor_entity == source
    assert vote.voter_person == source
    
    merge_rec.refresh_from_db()
    assert merge_rec.is_reversed is True
