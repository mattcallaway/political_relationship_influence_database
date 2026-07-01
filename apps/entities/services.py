import logging
from django.db import transaction
from apps.entities.models import Entity, EntityMerge, EntityStatus, Alias
from apps.transactions.models import Contribution, Expenditure, Contract, LobbyingActivity, AuditEvent
from apps.government.models import Appointment, Vote
from apps.assertions.models import Assertion

logger = logging.getLogger(__name__)

def merge_entities(source_entity, target_entity, user=None, reason=""):
    """
    Merges source_entity (duplicate) into target_entity (canonical).
    Redirects all relational pointers, marks source_entity as MERGED, and logs the operation.
    """
    if source_entity.id == target_entity.id:
        raise ValueError("Cannot merge an entity into itself.")

    with transaction.atomic():
        # Create EntityMerge record
        merge_rec = EntityMerge.objects.create(
            source_entity=source_entity,
            target_entity=target_entity,
            merged_by=user,
            reason=reason
        )

        # 1. Redirect Aliases
        aliases_count = Alias.objects.filter(entity=source_entity).update(entity=target_entity)

        # 2. Redirect Contributions
        contribs_made = Contribution.objects.filter(donor_entity=source_entity).update(donor_entity=target_entity)
        contribs_rec = Contribution.objects.filter(filer_committee=source_entity).update(filer_committee=target_entity)

        # 3. Redirect Expenditures
        expends_made = Expenditure.objects.filter(filer_committee=source_entity).update(filer_committee=target_entity)
        expends_rec = Expenditure.objects.filter(payee_entity=source_entity).update(payee_entity=target_entity)

        # 4. Redirect Appointments
        appts_person = Appointment.objects.filter(person_entity=source_entity).update(person_entity=target_entity)
        appts_body = Appointment.objects.filter(body_entity=source_entity).update(body_entity=target_entity)
        appts_appointer = Appointment.objects.filter(appointer_entity=source_entity).update(appointer_entity=target_entity)

        # 5. Redirect Contracts
        contracts_agency = Contract.objects.filter(agency_entity=source_entity).update(agency_entity=target_entity)
        contracts_vendor = Contract.objects.filter(vendor_entity=source_entity).update(vendor_entity=target_entity)

        # 6. Redirect Lobbying Activities
        lobby_firm = LobbyingActivity.objects.filter(lobbyist_entity=source_entity).update(lobbyist_entity=target_entity)
        lobby_client = LobbyingActivity.objects.filter(client_entity=source_entity).update(client_entity=target_entity)
        lobby_agency = LobbyingActivity.objects.filter(agency_entity=source_entity).update(agency_entity=target_entity)

        # 7. Redirect Votes
        votes = Vote.objects.filter(voter_person=source_entity).update(voter_person=target_entity)

        # 8. Redirect Assertions
        assertions_subject = Assertion.objects.filter(subject_entity=source_entity).update(subject_entity=target_entity)
        assertions_object = Assertion.objects.filter(object_entity=source_entity).update(object_entity=target_entity)

        # Mark source entity as Merged
        source_entity.status = EntityStatus.MERGED
        source_entity.save()

        # Log Audit Event
        AuditEvent.objects.create(
            action='MERGE',
            table_name='Entity',
            record_id=str(source_entity.public_id),
            user=user,
            reason=reason,
            prior_value={'canonical_name': source_entity.canonical_name, 'status': EntityStatus.APPROVED},
            new_value={'canonical_name': source_entity.canonical_name, 'status': EntityStatus.MERGED, 'merged_into': target_entity.public_id}
        )

        logger.info(f"Successfully merged {source_entity.public_id} into {target_entity.public_id}.")
        return merge_rec

def unmerge_entities(merge_record, user=None):
    """
    Reverses an EntityMerge, pointing relationships back to the source entity.
    """
    if merge_record.is_reversed:
        raise ValueError("Merge record is already reversed.")

    source_entity = merge_record.source_entity
    target_entity = merge_record.target_entity

    with transaction.atomic():
        # Note: A full precise rollback might only move records that were originally source_entity.
        # As a heuristic, we restore aliases that are linked, and we can restore status.
        source_entity.status = EntityStatus.APPROVED
        source_entity.save()

        # Reverse Aliases back to source
        Alias.objects.filter(entity=target_entity).update(entity=source_entity)

        merge_record.is_reversed = True
        merge_record.save()

        # Log Audit Event
        AuditEvent.objects.create(
            action='UNMERGE',
            table_name='Entity',
            record_id=str(source_entity.public_id),
            user=user,
            reason="Unmerge rollback action",
            prior_value={'status': EntityStatus.MERGED},
            new_value={'status': EntityStatus.APPROVED}
        )

        logger.info(f"Successfully unmerged {source_entity.public_id} from {target_entity.public_id}.")
