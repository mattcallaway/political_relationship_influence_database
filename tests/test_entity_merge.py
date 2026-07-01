import pytest
from django.contrib.auth import get_user_model
from apps.entities.models import Entity, EntityType, EntityStatus, EntityMerge
from apps.entities.services import merge_entities, unmerge_entities
from apps.government.models import Appointment, GovernmentBody
from apps.transactions.models import Contribution, AuditEvent
from apps.campaigns.models import Committee

User = get_user_model()

@pytest.mark.django_db
def test_entity_merge_and_unmerge():
    # 1. Setup Entities
    source_ent = Entity.objects.create(
        public_id="ENT999001",
        canonical_name="Robert L. Muelrath",
        entity_type=EntityType.PERSON,
        status=EntityStatus.APPROVED
    )
    target_ent = Entity.objects.create(
        public_id="ENT999002",
        canonical_name="Robert Muelrath",
        entity_type=EntityType.PERSON,
        status=EntityStatus.APPROVED
    )
    
    body_ent = Entity.objects.create(
        public_id="ENT999003",
        canonical_name="Board of Supervisors",
        entity_type=EntityType.GOVERNMENT_BODY,
        status=EntityStatus.VERIFIED
    )
    gov_body = GovernmentBody.objects.create(
        entity=body_ent,
        body_name="Board of Supervisors"
    )

    # 2. Setup Appointment
    appt = Appointment.objects.create(
        public_id="APT999001",
        person_entity=source_ent,
        body_entity=body_ent,
        start_date="2026-01-01"
    )

    # 3. Setup Contribution
    comm_ent = Entity.objects.create(
        public_id="ENT999004",
        canonical_name="Committee to Elect Gore",
        entity_type=EntityType.COMMITTEE,
        status=EntityStatus.VERIFIED
    )
    committee = Committee.objects.create(
        entity=comm_ent,
        committee_name="Committee to Elect Gore",
        public_id="COM999001"
    )
    contrib = Contribution.objects.create(
        public_id="CON999001",
        donor_entity=source_ent,
        filer_committee=comm_ent,
        amount=1000.00,
        schedule="Schedule A"
    )

    # Verify initial associations
    assert appt.person_entity == source_ent
    assert contrib.donor_entity == source_ent

    # 4. Perform Merge
    merge_rec = merge_entities(source_ent, target_ent, reason="Duplicate entity merge test")

    # Refresh from database
    appt.refresh_from_db()
    contrib.refresh_from_db()
    source_ent.refresh_from_db()

    # Assertions post-merge
    assert source_ent.status == EntityStatus.MERGED
    assert appt.person_entity == target_ent
    assert contrib.donor_entity == target_ent

    # Assert EntityMerge and AuditEvent
    assert EntityMerge.objects.count() == 1
    assert AuditEvent.objects.filter(action='MERGE').exists()

    # 5. Perform Unmerge
    unmerge_entities(merge_rec)
    source_ent.refresh_from_db()

    # Assertions post-unmerge
    assert source_ent.status == EntityStatus.APPROVED
    assert AuditEvent.objects.filter(action='UNMERGE').exists()
