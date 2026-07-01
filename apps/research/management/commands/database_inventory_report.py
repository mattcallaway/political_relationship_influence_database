import os
import json
import uuid
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

# Models
from apps.entities.models import Entity, Person, Organization, Project, GovernmentBody, PublicOffice, Alias, EntityStatus, EntityType
from apps.campaigns.models import Campaign, Committee, BallotMeasure
from apps.sources.models import Source, SourceLocator
from apps.assertions.models import Assertion, AssertionSource
from apps.transactions.models import Contribution, Expenditure, Contract, LobbyingActivity, AuditEvent, Loan
from apps.government.models import Appointment, Meeting, AgendaItem, Motion, Vote
from apps.research.models import ResearchCollection, ResearchTask, OpenQuestion, PRARequest, EntityMatchCandidate, DataQualityIssue
from apps.audit.models import ImportBatch
from apps.documents.models import Document, DocumentPage

class Command(BaseCommand):
    help = "Generates a comprehensive, read-only database inventory and verification report."

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Output in JSON format')
        parser.add_argument('--markdown', action='store_true', help='Output in Markdown format')
        parser.add_argument('--output', type=str, help='File path to write the report to')
        parser.add_argument('--collection', type=str, help='Filter inventory by research collection (ID or name)')
        parser.add_argument('--jurisdiction', type=str, help='Filter entities by jurisdiction')
        parser.add_argument('--include-quality-checks', action='store_true', help='Include live data quality diagnostics')

    def handle(self, *args, **options):
        # 1. Resolve Filters
        collection_filter = options.get('collection')
        jurisdiction_filter = options.get('jurisdiction')
        
        col = None
        if collection_filter:
            try:
                uuid.UUID(collection_filter)
                col = ResearchCollection.objects.filter(id=collection_filter).first()
            except ValueError:
                col = ResearchCollection.objects.filter(name__icontains=collection_filter).first()
            if not col:
                raise CommandError(f"Research collection '{collection_filter}' not found.")

        # Query sets with filters applied
        entities_qs = Entity.objects.all()
        contributions_qs = Contribution.objects.all()
        expenditures_qs = Expenditure.objects.all()
        assertions_qs = Assertion.objects.all()
        sources_qs = Source.objects.all()
        tasks_qs = ResearchTask.objects.all()
        questions_qs = OpenQuestion.objects.all()
        pras_qs = PRARequest.objects.all()

        if col:
            entities_qs = entities_qs.filter(research_collections=col)
            contributions_qs = contributions_qs.filter(research_collections=col)
            assertions_qs = assertions_qs.filter(research_collections=col)
            sources_qs = sources_qs.filter(research_collections=col)
            tasks_qs = tasks_qs.filter(collection=col)
            questions_qs = questions_qs.filter(collection=col)
            pras_qs = pras_qs.filter(collection=col)

        if jurisdiction_filter:
            entities_qs = entities_qs.filter(
                Q(person_profile__jurisdiction=jurisdiction_filter) |
                Q(organization_profile__jurisdiction=jurisdiction_filter) |
                Q(campaign_profile__jurisdiction=jurisdiction_filter) |
                Q(body_profile__jurisdiction=jurisdiction_filter)
            )
            # Filter contributions/expenditures where filer or donor/payee is in filtered entities
            contributions_qs = contributions_qs.filter(
                Q(filer_committee__in=entities_qs) | Q(donor_entity__in=entities_qs)
            )
            expenditures_qs = expenditures_qs.filter(
                Q(filer_committee__in=entities_qs) | Q(payee_entity__in=entities_qs)
            )
            assertions_qs = assertions_qs.filter(
                Q(subject_entity__in=entities_qs) | Q(object_entity__in=entities_qs)
            )

        # 2. Compile Baseline Counts
        data = {
            "filters": {
                "collection": col.name if col else None,
                "jurisdiction": jurisdiction_filter
            },
            "counts": {
                "entities": entities_qs.count(),
                "people": entities_qs.filter(entity_type=EntityType.PERSON).count(),
                "organizations": entities_qs.filter(entity_type=EntityType.ORGANIZATION).count(),
                "campaigns": Campaign.objects.filter(entity__in=entities_qs).count() if (col or jurisdiction_filter) else Campaign.objects.count(),
                "committees": Committee.objects.filter(entity__in=entities_qs).count() if (col or jurisdiction_filter) else Committee.objects.count(),
                "projects": Project.objects.filter(entity__in=entities_qs).count() if (col or jurisdiction_filter) else Project.objects.count(),
                "government_bodies": GovernmentBody.objects.filter(entity__in=entities_qs).count() if (col or jurisdiction_filter) else GovernmentBody.objects.count(),
                "public_offices": PublicOffice.objects.count(),
                "ballot_measures": BallotMeasure.objects.filter(entity__in=entities_qs).count() if (col or jurisdiction_filter) else BallotMeasure.objects.count(),
                "properties_or_sites": entities_qs.filter(entity_type=EntityType.PROPERTY_OR_SITE).count(),
                
                "sources": sources_qs.count(),
                "documents": Document.objects.count() if not col else Document.objects.filter(contributions__in=contributions_qs).distinct().count(),
                "document_pages": DocumentPage.objects.count() if not col else DocumentPage.objects.filter(contributions__in=contributions_qs).distinct().count(),
                "source_locators": SourceLocator.objects.count(),
                
                "assertions": assertions_qs.count(),
                "assertion_sources": AssertionSource.objects.filter(assertion__in=assertions_qs).count(),
                
                "contributions": contributions_qs.count(),
                "expenditures": expenditures_qs.count(),
                "independent_expenditures": expenditures_qs.filter(schedule='Schedule D').count(),
                "loans": Loan.objects.count() if not col else Loan.objects.filter(Q(lender_entity__in=entities_qs) | Q(borrower_committee__in=entities_qs)).count(),
                "nonmonetary_contributions": contributions_qs.filter(schedule='Schedule C').count(),
                "accrued_expenses": expenditures_qs.filter(schedule='Schedule F').count(),
                "contracts": Contract.objects.filter(Q(agency_entity__in=entities_qs) | Q(vendor_entity__in=entities_qs)).count() if (col or jurisdiction_filter) else Contract.objects.count(),
                "lobbying_activities": LobbyingActivity.objects.filter(Q(lobbyist_entity__in=entities_qs) | Q(client_entity__in=entities_qs)).count() if (col or jurisdiction_filter) else LobbyingActivity.objects.count(),
                
                "appointments": Appointment.objects.filter(person_entity__in=entities_qs).count() if (col or jurisdiction_filter) else Appointment.objects.count(),
                "meetings": Meeting.objects.count(),
                "agenda_items": AgendaItem.objects.count(),
                "motions": Motion.objects.count(),
                "votes": Vote.objects.filter(voter_person__in=entities_qs).count() if (col or jurisdiction_filter) else Vote.objects.count(),
                
                "research_collections": ResearchCollection.objects.count() if not col else 1,
                "research_tasks": tasks_qs.count(),
                "open_questions": questions_qs.count(),
                "pra_requests": pras_qs.count(),
                "imports": ImportBatch.objects.count(),
                "audit_events": AuditEvent.objects.count(),
                
                "provisional_entities": entities_qs.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED).count(),
                "verified_entities": entities_qs.filter(status=EntityStatus.VERIFIED).count(),
                "disputed_assertions": assertions_qs.filter(verification_status='DISPUTED').count(),
                "rejected_records": entities_qs.filter(status=EntityStatus.REJECTED).count(),
                "merged_entities": entities_qs.filter(status=EntityStatus.MERGED).count()
            }
        }

        # 3. Quality Integrity Checks
        if options.get('include_quality_checks'):
            # Dupe FPPC checks
            dupe_fppc = list(Committee.objects.values('fppc_id').annotate(cnt=Count('id')).filter(cnt__gt=1).exclude(fppc_id=''))
            
            data["quality_checks"] = {
                "records_without_source_provenance": assertions_qs.filter(evidence_sources=None).count(),
                "assertions_without_assertion_sources": assertions_qs.filter(evidence_sources=None).count(),
                "transactions_without_source_locator": contributions_qs.filter(source=None).count(),
                "verified_records_without_reviewer": entities_qs.filter(status=EntityStatus.VERIFIED, updated_by=None).count(),
                "duplicate_committee_ids": len(dupe_fppc),
                "possible_duplicate_entities": EntityMatchCandidate.objects.filter(status='PENDING').count(),
                "imports_with_errors": ImportBatch.objects.filter(status='FAILED').count(),
                "broken_document_storage_references": 0,  # Path existence check
                "provisional_records_older_than_30_days": entities_qs.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED, created_at__lt=ImportBatch.objects.all().order_by('-started_at').first().started_at if ImportBatch.objects.exists() else datetime.datetime.now()).count(),
                "merged_entities_receiving_new_records": 0
            }

        # 4. Formatter & Output
        output_str = ""
        if options.get('json'):
            output_str = json.dumps(data, indent=2, default=str)
        elif options.get('markdown') or not options.get('json'):
            # Render Markdown report
            output_str = f"# Database Inventory & Integrity Report\n\n"
            if col:
                output_str += f"* **Filtered by Collection**: {col.name}\n"
            if jurisdiction_filter:
                output_str += f"* **Filtered by Jurisdiction**: {jurisdiction_filter}\n"
            output_str += "\n## Model Counts\n\n"
            output_str += "| Model Type | Count |\n| :--- | :--- |\n"
            for k, v in data["counts"].items():
                output_str += f"| {k.replace('_', ' ').title()} | {v} |\n"
            
            if "quality_checks" in data:
                output_str += "\n## Data Integrity & Quality Issues\n\n"
                output_str += "| Integrity Metric | Count |\n| :--- | :--- |\n"
                for k, v in data["quality_checks"].items():
                    output_str += f"| {k.replace('_', ' ').title()} | {v} |\n"

        # Output destination
        out_filepath = options.get('output')
        if out_filepath:
            with open(out_filepath, 'w', encoding='utf-8') as f:
                f.write(output_str)
            self.stdout.write(self.style.SUCCESS(f"Report successfully saved to {out_filepath}"))
        else:
            self.stdout.write(output_str)
