import os
import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.audit.models import ControlledVocabularyValue, LegacyIdentifier, ImportBatch, ImportRow
from apps.entities.models import Entity, Person, Organization, Alias, EntityType, EntityStatus
from apps.sources.models import Source
from apps.assertions.models import Assertion, AssertionSource
from apps.transactions.models import Contribution, Expenditure
from apps.research.models import ResearchTask, PRARequest

class Command(BaseCommand):
    help = "Import seed content from the authentic v5 consolidated research Excel workbook."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/imports/Sonoma_Political_Influence_Database_v5_consolidated.xlsx',
            help='Path to the v5 consolidated Excel file.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a trial run with no schema changes saved.'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Workbook file not found at {file_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting v5 workbook import (dry_run={dry_run}) from {file_path}"))
        
        wb = openpyxl.load_workbook(file_path, data_only=True)
        batch = ImportBatch.objects.create(
            batch_name=f"V5_Import_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            source_file=file_path,
            is_dry_run=dry_run,
            status='IN_PROGRESS'
        )

        counts = {
            'Controlled_Vocabularies': 0,
            'Entities': 0,
            'Persons': 0,
            'Organizations': 0,
            'Sources': 0,
            'Assertions': 0,
            'Contributions': 0,
            'Expenditures': 0,
            'Legacy_IDs': 0,
            'Errors': 0
        }

        try:
            with transaction.atomic():
                # 1. Reference Data & Vocabularies
                if 'Reference_Data' in wb.sheetnames:
                    ws = wb['Reference_Data']
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        cat, code, label = str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip()
                        defn = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
                        if not dry_run:
                            ControlledVocabularyValue.objects.get_or_create(
                                category=cat, code=code,
                                defaults={'label': label, 'definition': defn}
                            )
                        counts['Controlled_Vocabularies'] += 1

                # 2. Entity Index
                sheet_entity = 'Entity_Index' if 'Entity_Index' in wb.sheetnames else 'Entities'
                if sheet_entity in wb.sheetnames:
                    ws = wb[sheet_entity]
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        pub_id = str(row[0]).strip()
                        etype = str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else 'ORGANIZATION'
                        name = str(row[2]).strip() if len(row) > 2 and row[2] is not None else pub_id
                        if etype not in ['PERSON', 'ORGANIZATION']:
                            etype = 'ORGANIZATION'
                        
                        if not dry_run:
                            entity, created = Entity.objects.get_or_create(
                                public_id=pub_id,
                                defaults={'canonical_name': name, 'entity_type': etype, 'status': EntityStatus.APPROVED}
                            )
                            if created:
                                counts['Entities'] += 1

                # 3. People
                sheet_p = 'People' if 'People' in wb.sheetnames else 'Persons'
                if sheet_p in wb.sheetnames:
                    ws = wb[sheet_p]
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        pub_id = str(row[0]).strip()
                        full_name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else pub_id
                        first = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
                        last = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
                        role = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ""
                        if not dry_run:
                            entity = Entity.objects.filter(public_id=pub_id).first()
                            if entity:
                                Person.objects.get_or_create(
                                    entity=entity,
                                    defaults={'display_name': full_name, 'first_name': first, 'last_name': last, 'public_role': role}
                                )
                                counts['Persons'] += 1

                # 4. Organizations
                if 'Organizations' in wb.sheetnames:
                    ws = wb['Organizations']
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        pub_id = str(row[0]).strip()
                        legal_name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else pub_id
                        org_type = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ""
                        if not dry_run:
                            entity = Entity.objects.filter(public_id=pub_id).first()
                            if entity:
                                Organization.objects.get_or_create(
                                    entity=entity,
                                    defaults={'legal_name': legal_name}
                                )
                                counts['Organizations'] += 1

                # 5. Sources
                if 'Sources' in wb.sheetnames:
                    ws = wb['Sources']
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        pub_id = str(row[0]).strip()
                        title = str(row[1]).strip() if len(row) > 1 and row[1] is not None else pub_id
                        stype = str(row[2]).strip() if len(row) > 2 and row[2] is not None else "OTHER"
                        if not dry_run:
                            Source.objects.get_or_create(
                                public_id=pub_id,
                                defaults={'title': title}
                            )
                            counts['Sources'] += 1

                # 6. Legacy Map
                sheet_leg = 'Legacy_ID_Map' if 'Legacy_ID_Map' in wb.sheetnames else 'Legacy_ID_Mappings'
                if sheet_leg in wb.sheetnames:
                    ws = wb[sheet_leg]
                    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                        if idx == 1 or not row or row[0] is None:
                            continue
                        leg_id = str(row[0]).strip()
                        curr_id = str(row[1]).strip() if len(row) > 1 and row[1] is not None else leg_id
                        model_target = str(row[2]).strip() if len(row) > 2 and row[2] is not None else 'Unknown'
                        if not dry_run:
                            LegacyIdentifier.objects.get_or_create(
                                legacy_id=leg_id,
                                defaults={'current_public_id': curr_id, 'target_model': model_target}
                            )
                            counts['Legacy_IDs'] += 1

                if dry_run:
                    transaction.set_rollback(True)

            batch.status = 'COMPLETED' if not dry_run else 'DRY_RUN_COMPLETED'
            batch.completed_at = timezone.now()
            batch.summary_counts = counts
            batch.save()

            self.stdout.write(self.style.SUCCESS(f"Import finished successfully! Summary: {counts}"))

        except Exception as e:
            batch.status = 'FAILED'
            batch.save()
            self.stderr.write(self.style.ERROR(f"Import failed with error: {str(e)}"))
            raise e
