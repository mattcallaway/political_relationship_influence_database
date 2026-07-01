import os
import json
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
import openpyxl

# Import Models
from apps.entities.models import Entity, Person, Organization, Project, GovernmentBody, PublicOffice, Alias, EntityStatus, EntityType
from apps.sources.models import Source, SourceLocator
from apps.campaigns.models import Campaign, Committee, BallotMeasure
from apps.transactions.models import Contribution, Expenditure, Contract, LobbyingActivity, AuditEvent, ReviewStatus
from apps.government.models import Appointment, Event, Vote
from apps.research.models import ResearchTask, OpenQuestion, PRARequest
from apps.audit.models import LegacyIdentifier, ImportBatch
from apps.assertions.models import Assertion, AssertionSource

User = get_user_model()

class RollbackException(Exception):
    pass

class Command(BaseCommand):
    help = "Imports consolidated research data from Sonoma_Political_Influence_Database_v5_consolidated.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/imports/Sonoma_Political_Influence_Database_v5_consolidated.xlsx',
            help='Path to the Excel file to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (runs imports in a transaction and rolls back at the end)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            raise CommandError(f"Excel file not found at: {file_path}")

        self.stdout.write(f"Starting import from: {file_path} (Dry Run: {dry_run})")
        
        # Load workbook
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            raise CommandError(f"Failed to load Excel file: {e}")

        # Metrics trackers
        imported_counts = {}
        row_errors = []
        
        # Create an import batch record
        batch_name = f"V5 Workbook Import - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Get or create a default user for creator/reviewer tags
        default_user, _ = User.objects.get_or_create(
            username='system_importer',
            defaults={'email': 'importer@system.local', 'is_staff': True}
        )

        try:
            with transaction.atomic():
                batch = ImportBatch.objects.create(
                    batch_name=batch_name,
                    source_file=file_path,
                    is_dry_run=dry_run,
                    imported_by=default_user,
                    status='IN_PROGRESS'
                )
                
                # Helper conversion functions
                def to_date(val):
                    if isinstance(val, datetime.datetime):
                        return val.date()
                    if isinstance(val, datetime.date):
                        return val
                    if isinstance(val, str) and val.strip():
                        try:
                            return datetime.datetime.strptime(val.strip(), "%Y-%m-%d").date()
                        except:
                            return None
                    return None

                def to_decimal(val):
                    if val is None:
                        return None
                    try:
                        return Decimal(str(val))
                    except:
                        return None

                def get_entity_by_pub_or_legacy(id_str):
                    if not id_str:
                        return None
                    id_str = str(id_str).strip()
                    # Try matching public_id first
                    ent = Entity.objects.filter(public_id=id_str).first()
                    if ent:
                        return ent
                    # Try matching legacy_id
                    legacy = LegacyIdentifier.objects.filter(legacy_id=id_str).first()
                    if legacy and legacy.entity:
                        return legacy.entity
                    return None

                def map_entity_status(status_str):
                    if not status_str:
                        return EntityStatus.PROVISIONAL_AUTO_CREATED
                    status_str = str(status_str).strip().upper()
                    if 'ACTIVE' in status_str or 'VERIFIED' in status_str:
                        return EntityStatus.VERIFIED
                    if 'NEEDS' in status_str:
                        return EntityStatus.NEEDS_REVIEW
                    if 'PROVISIONAL' in status_str or 'AUTO' in status_str:
                        return EntityStatus.PROVISIONAL_AUTO_CREATED
                    return EntityStatus.VERIFIED

                # ----------------- 1. SOURCES SHEET -----------------
                if 'Sources' in wb.sheetnames:
                    sheet = wb['Sources']
                    imported_counts['Sources'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]: # Skip empty rows
                            continue
                        try:
                            source_id = str(row[0]).strip()
                            title = str(row[1] or f"Source {source_id}").strip()
                            stype = str(row[2] or 'OTHER').strip()
                            publisher = str(row[3] or '').strip()
                            author = str(row[4] or '').strip()
                            pub_date = to_date(row[5])
                            access_date = to_date(row[6])
                            url = str(row[7] or '').strip()
                            arch_url = str(row[8] or '').strip()
                            jurisdiction = str(row[10] or 'Sonoma County').strip()
                            notes = str(row[13] or '').strip()

                            source, created = Source.objects.update_or_create(
                                public_id=source_id,
                                defaults={
                                    'title': title,
                                    'source_type': stype,
                                    'issuing_body': publisher,
                                    'author': author,
                                    'publication_date': pub_date,
                                    'access_date': access_date,
                                    'original_url': url,
                                    'archive_url': arch_url,
                                    'jurisdiction': jurisdiction,
                                    'notes': notes,
                                    'created_by': default_user
                                }
                            )
                            if created:
                                imported_counts['Sources'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Sources', 'row': row_idx, 'error': str(e)})

                # ----------------- 2. ENTITY INDEX SHEET -----------------
                if 'Entity_Index' in wb.sheetnames:
                    sheet = wb['Entity_Index']
                    imported_counts['Entity_Index'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            entity_id = str(row[0]).strip()
                            etype = str(row[1]).strip().upper()
                            name = str(row[2]).strip()
                            status = map_entity_status(row[3])
                            jurisdiction = str(row[4] or 'Sonoma County').strip()
                            notes = str(row[7] or '').strip()

                            entity, created = Entity.objects.update_or_create(
                                public_id=entity_id,
                                defaults={
                                    'entity_type': etype,
                                    'canonical_name': name,
                                    'normalized_name': name.lower().strip(),
                                    'status': status,
                                    'jurisdiction': jurisdiction,
                                    'created_by': default_user
                                }
                            )
                            # Create or update legacy map entry
                            LegacyIdentifier.objects.update_or_create(
                                legacy_id=entity_id,
                                defaults={
                                    'entity': entity,
                                    'current_public_id': entity_id,
                                    'target_model': 'Entity',
                                    'originating_system': 'v5_workbook',
                                    'source_workbook': 'Sonoma_Political_Influence_Database_v5_consolidated.xlsx',
                                    'import_batch': batch
                                }
                            )
                            if created:
                                imported_counts['Entity_Index'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Entity_Index', 'row': row_idx, 'error': str(e)})

                # ----------------- 3. PEOPLE SHEET -----------------
                if 'People' in wb.sheetnames:
                    sheet = wb['People']
                    imported_counts['People'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            person_id = str(row[0]).strip()
                            full_name = str(row[1]).strip()
                            fname = str(row[2] or '').strip()
                            mname = str(row[3] or '').strip()
                            lname = str(row[4] or '').strip()
                            suffix = str(row[5] or '').strip()
                            role = str(row[6] or '').strip()
                            notes = str(row[11] or '').strip()

                            entity = get_entity_by_pub_or_legacy(person_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=person_id,
                                    entity_type=EntityType.PERSON,
                                    canonical_name=full_name,
                                    normalized_name=full_name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )
                                LegacyIdentifier.objects.get_or_create(
                                    legacy_id=person_id,
                                    defaults={
                                        'entity': entity,
                                        'current_public_id': person_id,
                                        'target_model': 'Entity',
                                        'originating_system': 'v5_workbook',
                                        'source_workbook': 'Sonoma_Political_Influence_Database_v5_consolidated.xlsx',
                                        'import_batch': batch
                                    }
                                )

                            person, created = Person.objects.update_or_create(
                                entity=entity,
                                defaults={
                                    'first_name': fname,
                                    'middle_name': mname,
                                    'last_name': lname,
                                    'suffix': suffix,
                                    'display_name': full_name,
                                    'public_role': role,
                                    'notes': notes
                                }
                            )
                            if created:
                                imported_counts['People'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'People', 'row': row_idx, 'error': str(e)})

                # ----------------- 4. ORGANIZATIONS SHEET -----------------
                if 'Organizations' in wb.sheetnames:
                    sheet = wb['Organizations']
                    imported_counts['Organizations'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            org_id = str(row[0]).strip()
                            name = str(row[1]).strip()
                            org_type = str(row[2] or '').strip()
                            desc = str(row[9] or '').strip()

                            entity = get_entity_by_pub_or_legacy(org_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=org_id,
                                    entity_type=EntityType.ORGANIZATION,
                                    canonical_name=name,
                                    normalized_name=name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )
                                LegacyIdentifier.objects.get_or_create(
                                    legacy_id=org_id,
                                    defaults={
                                        'entity': entity,
                                        'current_public_id': org_id,
                                        'target_model': 'Entity',
                                        'originating_system': 'v5_workbook',
                                        'source_workbook': 'Sonoma_Political_Influence_Database_v5_consolidated.xlsx',
                                        'import_batch': batch
                                    }
                                )

                            org, created = Organization.objects.update_or_create(
                                entity=entity,
                                defaults={
                                    'legal_name': name,
                                    'common_name': name,
                                    'org_category': org_type,
                                    'notes': desc
                                }
                            )
                            if created:
                                imported_counts['Organizations'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Organizations', 'row': row_idx, 'error': str(e)})

                # ----------------- 5. ALIASES SHEET -----------------
                if 'Aliases' in wb.sheetnames:
                    sheet = wb['Aliases']
                    imported_counts['Aliases'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            entity_id = str(row[1]).strip()
                            alias_text = str(row[2]).strip()
                            atype = str(row[3] or 'ALT_NAME').strip()
                            source_id = str(row[6] or '').strip()

                            entity = get_entity_by_pub_or_legacy(entity_id)
                            if not entity:
                                raise ValueError(f"Parent Entity {entity_id} not found for alias.")

                            source_locator = None
                            if source_id:
                                source = Source.objects.filter(public_id=source_id).first()
                                if source:
                                    source_locator = SourceLocator.objects.create(
                                        source=source,
                                        locator_description="Workbook Alias Source Reference"
                                    )

                            alias, created = Alias.objects.update_or_create(
                                entity=entity,
                                alias_text=alias_text,
                                defaults={
                                    'normalized_alias': alias_text.lower().strip(),
                                    'alias_type': atype,
                                    'source_locator': source_locator
                                }
                            )
                            if created:
                                imported_counts['Aliases'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Aliases', 'row': row_idx, 'error': str(e)})

                # ----------------- 6. CAMPAIGNS SHEET -----------------
                if 'Campaigns' in wb.sheetnames:
                    sheet = wb['Campaigns']
                    imported_counts['Campaigns'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            campaign_id = str(row[0]).strip()
                            camp_name = str(row[1]).strip()
                            ctype = str(row[2] or 'Candidate campaign').strip()
                            cand_id = str(row[3] or '').strip()
                            comm_id = str(row[4] or '').strip()
                            office_id = str(row[5] or '').strip()
                            outcome = str(row[9] or '').strip()

                            entity = get_entity_by_pub_or_legacy(campaign_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=campaign_id,
                                    entity_type=EntityType.CAMPAIGN,
                                    canonical_name=camp_name,
                                    normalized_name=camp_name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )

                            candidate_ent = get_entity_by_pub_or_legacy(cand_id)
                            office_ent = get_entity_by_pub_or_legacy(office_id)
                            committee_ent = get_entity_by_pub_or_legacy(comm_id)

                            if not candidate_ent:
                                # Fallback placeholder
                                candidate_ent = entity

                            if not office_ent:
                                office_ent = entity

                            campaign, created = Campaign.objects.update_or_create(
                                public_id=campaign_id,
                                defaults={
                                    'entity': entity,
                                    'candidate': candidate_ent,
                                    'office': office_ent,
                                    'election_year': 2026, # default fallback
                                    'campaign_name': camp_name,
                                    'committee': committee_ent,
                                    'outcome': outcome
                                }
                            )
                            if created:
                                imported_counts['Campaigns'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Campaigns', 'row': row_idx, 'error': str(e)})

                # ----------------- 7. COMMITTEES SHEET -----------------
                if 'Committees' in wb.sheetnames:
                    sheet = wb['Committees']
                    imported_counts['Committees'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            comm_id = str(row[0]).strip()
                            name = str(row[1]).strip()
                            ctype = str(row[2] or '').strip()
                            fppc = str(row[3] or '').strip()
                            officer_id = str(row[6] or '').strip()

                            entity = get_entity_by_pub_or_legacy(comm_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=comm_id,
                                    entity_type=EntityType.COMMITTEE,
                                    canonical_name=name,
                                    normalized_name=name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )

                            officer_ent = get_entity_by_pub_or_legacy(officer_id)

                            committee, created = Committee.objects.update_or_create(
                                public_id=comm_id,
                                defaults={
                                    'entity': entity,
                                    'fppc_id': fppc,
                                    'committee_type': ctype,
                                    'committee_name': name,
                                    'controlling_candidate': officer_ent
                                }
                            )
                            if created:
                                imported_counts['Committees'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Committees', 'row': row_idx, 'error': str(e)})

                # ----------------- 8. PROJECTS SHEET -----------------
                if 'Projects' in wb.sheetnames:
                    sheet = wb['Projects']
                    imported_counts['Projects'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            project_id = str(row[0]).strip()
                            name = str(row[1]).strip()
                            ptype = str(row[2] or '').strip()
                            juris = str(row[3] or 'Sonoma County').strip()
                            loc = str(row[4] or '').strip()
                            applicant_id = str(row[5] or '').strip()
                            owner_id = str(row[6] or '').strip()
                            status = str(row[8] or 'PROPOSED').strip()

                            entity = get_entity_by_pub_or_legacy(project_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=project_id,
                                    entity_type=EntityType.DEVELOPMENT_PROJECT,
                                    canonical_name=name,
                                    normalized_name=name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )

                            applicant_ent = get_entity_by_pub_or_legacy(applicant_id)
                            owner_ent = get_entity_by_pub_or_legacy(owner_id)

                            project, created = Project.objects.update_or_create(
                                entity=entity,
                                defaults={
                                    'project_category': ptype,
                                    'jurisdiction': juris,
                                    'location': loc,
                                    'applicant': applicant_ent,
                                    'property_owner': owner_ent,
                                    'status': status
                                }
                            )
                            if created:
                                imported_counts['Projects'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Projects', 'row': row_idx, 'error': str(e)})

                # ----------------- 9. GOVERNMENT BODIES -----------------
                if 'Government_Bodies' in wb.sheetnames:
                    sheet = wb['Government_Bodies']
                    imported_counts['Government_Bodies'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            body_id = str(row[0]).strip()
                            name = str(row[1]).strip()
                            btype = str(row[2] or '').strip()
                            juris = str(row[3] or 'Sonoma County').strip()

                            entity = get_entity_by_pub_or_legacy(body_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=body_id,
                                    entity_type=EntityType.GOVERNMENT_BODY,
                                    canonical_name=name,
                                    normalized_name=name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )

                            gov, created = GovernmentBody.objects.update_or_create(
                                entity=entity,
                                defaults={
                                    'body_type': btype,
                                    'jurisdiction': juris
                                }
                            )
                            if created:
                                imported_counts['Government_Bodies'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Government_Bodies', 'row': row_idx, 'error': str(e)})

                # ----------------- 10. PUBLIC OFFICES -----------------
                if 'Public_Offices' in wb.sheetnames:
                    sheet = wb['Public_Offices']
                    imported_counts['Public_Offices'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            office_id = str(row[0]).strip()
                            name = str(row[1]).strip()
                            juris = str(row[3] or 'Sonoma County').strip()
                            elect_code = str(row[5] or '').strip()

                            entity = get_entity_by_pub_or_legacy(office_id)
                            if not entity:
                                entity = Entity.objects.create(
                                    public_id=office_id,
                                    entity_type=EntityType.PUBLIC_OFFICE,
                                    canonical_name=name,
                                    normalized_name=name.lower().strip(),
                                    status=EntityStatus.VERIFIED,
                                    created_by=default_user
                                )

                            office, created = PublicOffice.objects.update_or_create(
                                entity=entity,
                                defaults={
                                    'office_name': name,
                                    'jurisdiction': juris,
                                    'elected_or_appointed': elect_code
                                }
                            )
                            if created:
                                imported_counts['Public_Offices'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Public_Offices', 'row': row_idx, 'error': str(e)})

                # ----------------- 11. ASSERTIONS SHEET -----------------
                if 'Assertions' in wb.sheetnames:
                    sheet = wb['Assertions']
                    imported_counts['Assertions'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            ast_id = str(row[0]).strip()
                            sub_id = str(row[1]).strip()
                            pred = str(row[2]).strip()
                            obj_id = str(row[3] or '').strip()
                            obj_val = str(row[4] or '').strip()
                            ctype = str(row[5] or 'FACTUAL').strip().upper()
                            start_dt = to_date(row[6])
                            end_dt = to_date(row[7])
                            vstatus = str(row[9] or 'UNVERIFIED').strip().upper()
                            notes = str(row[15] or '').strip()

                            sub_ent = get_entity_by_pub_or_legacy(sub_id)
                            obj_ent = get_entity_by_pub_or_legacy(obj_id) if obj_id else None

                            if not sub_ent:
                                raise ValueError(f"Subject Entity {sub_id} not found.")

                            ast, created = Assertion.objects.update_or_create(
                                public_id=ast_id,
                                defaults={
                                    'subject_entity': sub_ent,
                                    'predicate': pred,
                                    'object_entity': obj_ent,
                                    'object_value': obj_val,
                                    'claim_type': ctype,
                                    'verification_status': vstatus,
                                    'effective_start': start_dt,
                                    'effective_end': end_dt,
                                    'explanatory_note': notes,
                                    'created_by': default_user
                                }
                            )
                            if created:
                                imported_counts['Assertions'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Assertions', 'row': row_idx, 'error': str(e)})

                # ----------------- 12. ASSERTION SOURCES -----------------
                if 'Assertion_Sources' in wb.sheetnames:
                    sheet = wb['Assertion_Sources']
                    imported_counts['Assertion_Sources'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            asrc_id = str(row[0]).strip()
                            ast_id = str(row[1]).strip()
                            src_id = str(row[2]).strip()
                            support = str(row[3] or 'PRIMARY').strip().upper()
                            loc_txt = str(row[4] or '').strip()
                            summary = str(row[5] or '').strip()

                            assertion = Assertion.objects.filter(public_id=ast_id).first()
                            source = Source.objects.filter(public_id=src_id).first()

                            if not assertion or not source:
                                raise ValueError(f"Assertion {ast_id} or Source {src_id} not found.")

                            source_locator = SourceLocator.objects.create(
                                source=source,
                                section=loc_txt,
                                locator_description=summary
                            )

                            asrc, created = AssertionSource.objects.get_or_create(
                                assertion=assertion,
                                source=source,
                                support_type=support,
                                defaults={
                                    'source_locator': source_locator,
                                    'evidence_note': summary,
                                    'reviewer': default_user
                                }
                            )
                            if created:
                                imported_counts['Assertion_Sources'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Assertion_Sources', 'row': row_idx, 'error': str(e)})

                # ----------------- 13. APPOINTMENTS SHEET -----------------
                if 'Appointments' in wb.sheetnames:
                    sheet = wb['Appointments']
                    imported_counts['Appointments'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            apt_id = str(row[0]).strip()
                            person_id = str(row[1]).strip()
                            office_id = str(row[2]).strip()
                            appointer_id = str(row[3] or '').strip()
                            apt_date = to_date(row[4])
                            start_dt = to_date(row[5])
                            end_dt = to_date(row[6])

                            person_ent = get_entity_by_pub_or_legacy(person_id)
                            office_ent = get_entity_by_pub_or_legacy(office_id)
                            appointer_ent = get_entity_by_pub_or_legacy(appointer_id) if appointer_id else None

                            if not person_ent or not office_ent:
                                raise ValueError(f"Person {person_id} or Office {office_id} not found.")

                            apt, created = Appointment.objects.update_or_create(
                                public_id=apt_id,
                                defaults={
                                    'person_entity': person_ent,
                                    'body_entity': office_ent,
                                    'appointer_entity': appointer_ent,
                                    'start_date': start_dt or apt_date,
                                    'end_date': end_dt
                                }
                            )
                            if created:
                                imported_counts['Appointments'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Appointments', 'row': row_idx, 'error': str(e)})

                # ----------------- 14. CONTRACTS SHEET -----------------
                if 'Contracts' in wb.sheetnames:
                    sheet = wb['Contracts']
                    imported_counts['Contracts'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            ctr_id = str(row[0]).strip()
                            gov_id = str(row[1]).strip()
                            vendor_id = str(row[2]).strip()
                            amt = to_decimal(row[7])
                            purpose = str(row[8] or '').strip()
                            ctr_date = to_date(row[4])

                            gov_ent = get_entity_by_pub_or_legacy(gov_id)
                            vendor_ent = get_entity_by_pub_or_legacy(vendor_id)

                            if not gov_ent or not vendor_ent:
                                raise ValueError(f"Gov {gov_id} or Vendor {vendor_id} not found.")

                            ctr, created = Contract.objects.update_or_create(
                                public_id=ctr_id,
                                defaults={
                                    'agency_entity': gov_ent,
                                    'vendor_entity': vendor_ent,
                                    'contract_title': purpose,
                                    'amount': amt,
                                    'execution_date': ctr_date
                                }
                            )
                            if created:
                                imported_counts['Contracts'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Contracts', 'row': row_idx, 'error': str(e)})

                # ----------------- 15. EVENTS SHEET -----------------
                if 'Events' in wb.sheetnames:
                    sheet = wb['Events']
                    imported_counts['Events'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            evt_id = str(row[0]).strip()
                            etype = str(row[1] or 'HEARING').strip()
                            evt_date = to_date(row[2])
                            loc = str(row[3] or 'Sonoma County').strip()
                            title = str(row[4] or f"Event {evt_id}").strip()
                            notes = str(row[10] or '').strip()

                            evt, created = Event.objects.update_or_create(
                                public_id=evt_id,
                                defaults={
                                    'event_name': title,
                                    'event_type': etype,
                                    'event_date': evt_date or datetime.date.today(),
                                    'location': loc,
                                    'summary': notes
                                }
                            )
                            if created:
                                imported_counts['Events'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Events', 'row': row_idx, 'error': str(e)})

                # ----------------- 16. RESEARCH QUEUE SHEET -----------------
                if 'Research_Queue' in wb.sheetnames:
                    sheet = wb['Research_Queue']
                    imported_counts['Research_Queue'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            rsr_id = str(row[0]).strip()
                            priority = str(row[1] or 'MEDIUM').strip().upper()
                            task = str(row[2]).strip()
                            status = str(row[7] or 'OPEN').strip().upper()
                            notes = str(row[11] or '').strip()

                            rtask, created = ResearchTask.objects.update_or_create(
                                public_id=rsr_id,
                                defaults={
                                    'task_title': task,
                                    'priority': priority,
                                    'status': status,
                                    'notes': notes
                                }
                            )
                            if created:
                                imported_counts['Research_Queue'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'Research_Queue', 'row': row_idx, 'error': str(e)})

                # ----------------- 17. PRA REQUESTS SHEET -----------------
                if 'PRA_Requests' in wb.sheetnames:
                    sheet = wb['PRA_Requests']
                    imported_counts['PRA_Requests'] = 0
                    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                        if not row[0]:
                            continue
                        try:
                            pra_id = str(row[0]).strip()
                            agency_id = str(row[1]).strip()
                            title = str(row[2]).strip()
                            summary = str(row[3] or '').strip()
                            sub_dt = to_date(row[4])
                            status = str(row[6] or 'DRAFT').strip().upper()

                            pra, created = PRARequest.objects.update_or_create(
                                public_id=pra_id,
                                defaults={
                                    'target_agency': agency_id,
                                    'request_summary': summary,
                                    'submission_date': sub_dt,
                                    'status': status,
                                    'tracking_number': title
                                }
                            )
                            if created:
                                imported_counts['PRA_Requests'] += 1
                        except Exception as e:
                            row_errors.append({'sheet': 'PRA_Requests', 'row': row_idx, 'error': str(e)})

                if dry_run:
                    raise RollbackException()

        except RollbackException:
            self.stdout.write(self.style.SUCCESS("DRY RUN MODE: Database transactions rolled back cleanly."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Import process failed: {e}"))
            raise

        # Generate Reports
        report_data = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'dry_run': dry_run,
            'imported_counts': imported_counts,
            'errors_count': len(row_errors),
            'errors': row_errors
        }
        
        # Write JSON Report
        os.makedirs('data/reports', exist_ok=True)
        with open('data/reports/v5-import-report.json', 'w') as f:
            json.dump(report_data, f, indent=4)
            
        # Write Markdown Report
        os.makedirs('docs', exist_ok=True)
        with open('docs/v5-import-report.md', 'w') as f:
            f.write(f"# V5 Consolidated Workbook Import Report\n\n")
            f.write(f"- **Import Time**: {report_data['timestamp']}\n")
            f.write(f"- **Dry Run Mode**: {report_data['dry_run']}\n")
            f.write(f"- **Total Rows Failed**: {report_data['errors_count']}\n\n")
            f.write(f"## Imported Counts By Sheet\n\n")
            f.write(f"| Sheet Name | Successful Imports Count |\n")
            f.write(f"| :--- | :--- |\n")
            for sheet, count in imported_counts.items():
                f.write(f"| {sheet} | {count} |\n")
            
            if row_errors:
                f.write(f"\n## Row Ingestion Failures\n\n")
                f.write(f"| Sheet | Row # | Error Details |\n")
                f.write(f"| :--- | :--- | :--- |\n")
                for err in row_errors[:50]: # cap at 50 in markdown
                    f.write(f"| {err['sheet']} | {err['row']} | {err['error']} |\n")

        self.stdout.write(self.style.SUCCESS("Reports successfully written to docs/v5-import-report.md and data/reports/v5-import-report.json"))
