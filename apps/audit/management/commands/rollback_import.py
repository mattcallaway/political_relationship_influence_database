import uuid
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from apps.audit.models import ImportBatch, LegacyIdentifier
from apps.entities.models import Entity, EntityStatus
from apps.transactions.models import Contribution, Expenditure

class Command(BaseCommand):
    help = "Safely rolls back and deletes all transactions and provisional entities created under a specific ImportBatch."

    def add_arguments(self, parser):
        parser.add_argument('batch_id', type=str, help='UUID of the ImportBatch to roll back')

    def handle(self, *args, **options):
        batch_id = options.get('batch_id')
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            raise CommandError(f"Invalid UUID format: {batch_id}")

        batch = ImportBatch.objects.filter(id=batch_uuid).first()
        if not batch:
            raise CommandError(f"ImportBatch with ID {batch_id} not found.")

        if batch.status == 'ROLLED_BACK':
            self.stdout.write(self.style.WARNING(f"ImportBatch '{batch.batch_name}' is already marked as ROLLED_BACK."))
            return

        self.stdout.write(f"Initiating rollback for ImportBatch: {batch.batch_name} ({batch.id})...")

        with transaction.atomic():
            # 1. Gather all Contributions & Expenditures to delete
            contribs = Contribution.objects.filter(import_batch=batch)
            contrib_count = contribs.count()
            
            expends = Expenditure.objects.filter(import_batch=batch)
            expend_count = expends.count()

            # 2. Gather entities linked to this batch via LegacyIdentifier
            legacy_ids = LegacyIdentifier.objects.filter(import_batch=batch)
            entities_to_check = [lid.entity for lid in legacy_ids if lid.entity]
            
            # Deletions of transactions
            contribs.delete()
            expends.delete()

            # 3. Assess and clean up provisional entities
            deleted_entity_count = 0
            for entity in entities_to_check:
                try:
                    entity.refresh_from_db()
                except Entity.DoesNotExist:
                    continue

                if entity.status == EntityStatus.PROVISIONAL_AUTO_CREATED:
                    # Reference safety checks
                    has_other_contribs = Contribution.objects.filter(Q(donor_entity=entity) | Q(filer_committee=entity)).exists()
                    has_other_expends = Expenditure.objects.filter(Q(payee_entity=entity) | Q(filer_committee=entity)).exists()
                    has_assertions = entity.subject_assertions.exists() or entity.object_assertions.exists()
                    
                    if not (has_other_contribs or has_other_expends or has_assertions):
                        entity.delete()
                        deleted_entity_count += 1

            # 4. Clean up LegacyIdentifiers
            legacy_id_count = legacy_ids.count()
            legacy_ids.delete()

            # 5. Mark batch as rolled back
            batch.status = 'ROLLED_BACK'
            batch.save()

            self.stdout.write(self.style.SUCCESS(
                f"Rollback completed successfully:\n"
                f"- Deleted {contrib_count} contributions\n"
                f"- Deleted {expend_count} expenditures\n"
                f"- Deleted {deleted_entity_count} orphaned provisional entities\n"
                f"- Deleted {legacy_id_count} legacy identifier records"
            ))
