from django.shortcuts import render
from apps.entities.models import Entity, EntityStatus
from apps.transactions.models import Contribution, ReviewStatus, AuditEvent
from apps.documents.models import Document

from django.shortcuts import render
from django.utils import timezone
import datetime
from django.db.models import Count

# Import Models
from apps.entities.models import Entity, Person, Organization, Project as ProjectSubtype, GovernmentBody as GovBodySubtype, PublicOffice as OfficeSubtype, EntityStatus, EntityMerge
from apps.campaigns.models import Campaign, Committee, BallotMeasure
from apps.sources.models import Source, SourceLocator
from apps.assertions.models import Assertion, AssertionSource
from apps.transactions.models import Contribution, Expenditure, Contract, LobbyingActivity, AuditEvent, ReviewStatus
from apps.government.models import Appointment, Meeting, AgendaItem, Motion, Vote
from apps.research.models import ResearchTask, OpenQuestion, PRARequest, ResearchCollection, EntityMatchCandidate
from apps.audit.models import ImportBatch
from apps.documents.models import Document

def research_dashboard(request):
    # Base Counts
    total_entities = Entity.objects.count()
    total_people = Entity.objects.filter(entity_type='PERSON').count()
    total_organizations = Entity.objects.filter(entity_type='ORGANIZATION').count()
    total_campaigns = Campaign.objects.count()
    total_committees = Committee.objects.count()
    total_projects = ProjectSubtype.objects.count()
    total_gov_bodies = GovBodySubtype.objects.count()
    total_offices = OfficeSubtype.objects.count()
    total_ballot_measures = BallotMeasure.objects.count()
    total_properties = Entity.objects.filter(entity_type='PROPERTY_OR_SITE').count()
    
    total_sources = Source.objects.count()
    total_docs = Document.objects.count()
    total_assertions = Assertion.objects.count()
    total_contributions = Contribution.objects.count()
    total_expenditures = Expenditure.objects.count()
    total_lobbying = LobbyingActivity.objects.count()
    total_contracts = Contract.objects.count()
    total_appointments = Appointment.objects.count()
    total_meetings = Meeting.objects.count()
    total_votes = Vote.objects.count()

    # Review status
    entities_verified = Entity.objects.filter(status=EntityStatus.VERIFIED).count()
    entities_reviewed = Entity.objects.filter(status=EntityStatus.REVIEWED).count()
    entities_auto_matched = Entity.objects.filter(status=EntityStatus.AUTO_MATCHED).count()
    entities_provisional = Entity.objects.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED).count()
    entities_rejected = Entity.objects.filter(status=EntityStatus.REJECTED).count()
    
    contribs_verified = Contribution.objects.filter(review_status=ReviewStatus.VERIFIED).count()
    contribs_auto_matched = Contribution.objects.filter(review_status=ReviewStatus.AUTO_MATCHED).count()
    contribs_needs_review = Contribution.objects.filter(review_status=ReviewStatus.NEEDS_REVIEW).count()
    contribs_auto_imported = Contribution.objects.filter(review_status=ReviewStatus.AUTO_IMPORTED).count()
    contribs_rejected = Contribution.objects.filter(review_status=ReviewStatus.REJECTED).count()
    
    possible_duplicates = EntityMatchCandidate.objects.filter(status='PENDING').count()
    disputed_assertions = Assertion.objects.filter(verification_status='DISPUTED').count()
    unresolved_locators = SourceLocator.objects.filter(assertion_sources=None).count()

    # Research activity
    open_tasks = ResearchTask.objects.filter(status='OPEN').count()
    high_priority_tasks = ResearchTask.objects.filter(priority='HIGH').count()
    total_collections = ResearchCollection.objects.count()
    pending_pras = PRARequest.objects.exclude(status='COMPLETED').count()
    
    recent_imports = ImportBatch.objects.all().order_by('-started_at')[:5]
    recent_entities = Entity.objects.all().order_by('-updated_at')[:5]
    recent_merges = EntityMerge.objects.all().order_by('-merged_at')[:5]
    recent_audits = AuditEvent.objects.all().order_by('-timestamp')[:10]

    # Data-quality indicators
    assertions_no_source = Assertion.objects.filter(assertion_sources=None).count()
    transactions_no_locator = Contribution.objects.filter(source=None).count()
    verified_no_reviewer = Entity.objects.filter(status=EntityStatus.VERIFIED, updated_by=None).count()
    
    # Simple check for duplicate committee FPPC IDs
    duplicate_committees_query = Committee.objects.values('fppc_id').annotate(id_count=Count('id')).filter(id_count__gt=1).exclude(fppc_id='')
    duplicate_committee_ids = len(duplicate_committees_query)
    
    missing_jurisdictions = Entity.objects.filter(jurisdiction='').count()
    
    stale_provisional_date = timezone.now() - datetime.timedelta(days=30)
    stale_provisional = Entity.objects.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED, created_at__lt=stale_provisional_date).count()

    return render(request, 'research/dashboard.html', {
        'total_entities': total_entities,
        'total_people': total_people,
        'total_organizations': total_organizations,
        'total_campaigns': total_campaigns,
        'total_committees': total_committees,
        'total_projects': total_projects,
        'total_gov_bodies': total_gov_bodies,
        'total_offices': total_offices,
        'total_ballot_measures': total_ballot_measures,
        'total_properties': total_properties,
        'total_sources': total_sources,
        'total_docs': total_docs,
        'total_assertions': total_assertions,
        'total_contributions': total_contributions,
        'total_expenditures': total_expenditures,
        'total_lobbying': total_lobbying,
        'total_contracts': total_contracts,
        'total_appointments': total_appointments,
        'total_meetings': total_meetings,
        'total_votes': total_votes,
        'entities_verified': entities_verified,
        'entities_reviewed': entities_reviewed,
        'entities_auto_matched': entities_auto_matched,
        'entities_provisional': entities_provisional,
        'entities_rejected': entities_rejected,
        'contribs_verified': contribs_verified,
        'contribs_auto_matched': contribs_auto_matched,
        'contribs_needs_review': contribs_needs_review,
        'contribs_auto_imported': contribs_auto_imported,
        'contribs_rejected': contribs_rejected,
        'possible_duplicates': possible_duplicates,
        'disputed_assertions': disputed_assertions,
        'unresolved_locators': unresolved_locators,
        'open_tasks': open_tasks,
        'high_priority_tasks': high_priority_tasks,
        'total_collections': total_collections,
        'pending_pras': pending_pras,
        'recent_imports': recent_imports,
        'recent_entities': recent_entities,
        'recent_merges': recent_merges,
        'recent_audits': recent_audits,
        'assertions_no_source': assertions_no_source,
        'transactions_no_locator': transactions_no_locator,
        'verified_no_reviewer': verified_no_reviewer,
        'duplicate_committee_ids': duplicate_committee_ids,
        'missing_jurisdictions': missing_jurisdictions,
        'stale_provisional': stale_provisional
    })

def research_tasks(request):
    from apps.research.models import ResearchTask, OpenQuestion, PRARequest
    tasks = ResearchTask.objects.all().order_by('-created_at')
    questions = OpenQuestion.objects.all()
    pras = PRARequest.objects.all()
    return render(request, 'research/research_tasks.html', {
        'tasks': tasks,
        'questions': questions,
        'pras': pras
    })

def data_quality(request):
    from apps.research.models import DataQualityIssue
    from apps.entities.models import Entity
    from apps.assertions.models import Assertion
    from apps.campaigns.models import Committee
    from django.contrib import messages
    from django.db import transaction
    from django.shortcuts import redirect
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'fix_jurisdictions':
            with transaction.atomic():
                updated = Entity.objects.filter(jurisdiction='').update(jurisdiction='Sonoma County')
                DataQualityIssue.objects.filter(issue_type="Missing Jurisdiction").update(is_resolved=True)
                messages.success(request, f"Successfully assigned 'Sonoma County' to {updated} entities!")
        elif action == 'fix_assertions':
            with transaction.atomic():
                updated = DataQualityIssue.objects.filter(issue_type="Missing Source Provenance").update(is_resolved=True)
                messages.success(request, "Provenance issues marked resolved!")
        return redirect('data_quality')

    # Clean old unresolved issues
    DataQualityIssue.objects.filter(is_resolved=False).delete()
    
    # 1. Missing jurisdiction
    no_jur = Entity.objects.filter(jurisdiction='')
    for ent in no_jur:
        DataQualityIssue.objects.get_or_create(
            issue_type="Missing Jurisdiction",
            description=f"Entity '{ent.canonical_name}' has an empty jurisdiction field.",
            affected_object_type="Entity",
            affected_object_id=str(ent.id)
        )
        
    # 2. Assertions without sources
    from django.db.models import Count
    no_src = Assertion.objects.annotate(src_count=Count('evidence_sources')).filter(src_count=0)
    for ast in no_src:
        DataQualityIssue.objects.get_or_create(
            issue_type="Missing Source Provenance",
            description=f"Assertion '{ast.public_id}' is not linked to any source coordinates.",
            affected_object_type="Assertion",
            affected_object_id=str(ast.id)
        )
        
    # 3. Committees with duplicate FPPC IDs
    dupe_fppc = Committee.objects.values('fppc_id').annotate(cnt=Count('id')).filter(cnt__gt=1).exclude(fppc_id='')
    for item in dupe_fppc:
        f_id = item['fppc_id']
        DataQualityIssue.objects.get_or_create(
            issue_type="Duplicate FPPC ID",
            description=f"Multiple committees are registered with the same FPPC ID: {f_id}.",
            affected_object_type="Committee",
            affected_object_id=f_id
        )
        
    issues = DataQualityIssue.objects.all().order_by('is_resolved', 'issue_type')
    return render(request, 'research/data_quality.html', {
        'issues': issues
    })

def imports_management(request):
    from apps.audit.models import ImportBatch
    batches = ImportBatch.objects.all().order_by('-started_at')
    return render(request, 'research/imports_management.html', {
        'batches': batches
    })

def collection_list(request):
    from apps.research.models import ResearchCollection
    
    # Auto-seed sample collection if none exist
    col, created = ResearchCollection.objects.get_or_create(
        name="Muelrath Public Affairs",
        defaults={
            'description': 'Lobbying, political consulting, and public relations campaign tracking in Sonoma County.'
        }
    )
    if created:
        from apps.entities.models import Entity
        for ent in Entity.objects.all()[:6]:
            col.entities.add(ent)
            
    collections = ResearchCollection.objects.all()
    return render(request, 'research/collection_list.html', {
        'collections': collections
    })

def collection_detail(request, collection_id):
    from apps.research.models import ResearchCollection
    from django.shortcuts import get_object_or_404
    collection = get_object_or_404(ResearchCollection, id=collection_id)
    
    # Relationships highlight (e.g. direct assertions linking entities inside the collection)
    entities = collection.entities.all()
    from apps.assertions.models import Assertion
    from django.db.models import Q
    assertions = Assertion.objects.filter(
        subject_entity__in=entities,
        object_entity__in=entities
    ).distinct()
    
    return render(request, 'research/collection_detail.html', {
        'collection': collection,
        'entities': entities,
        'assertions': assertions,
        'sources': collection.sources.all(),
        'contributions': collection.contributions.all(),
        'tasks': collection.tasks.all(),
        'questions': collection.questions.all(),
        'pra_requests': collection.pra_requests.all()
    })

def network_explorer(request):
    from apps.entities.models import Entity
    from apps.assertions.models import Assertion
    import json
    
    entities = Entity.objects.exclude(status='MERGED')
    assertions = Assertion.objects.filter(object_entity__isnull=False)
    
    # Compile Cytoscape nodes
    nodes = []
    for ent in entities:
        nodes.append({
            'data': {
                'id': ent.public_id,
                'label': ent.canonical_name,
                'type': ent.entity_type,
                'status': ent.status
            }
        })
        
    # Compile Cytoscape edges
    edges = []
    for ast in assertions:
        edges.append({
            'data': {
                'id': ast.public_id,
                'source': ast.subject_entity.public_id,
                'target': ast.object_entity.public_id,
                'label': ast.predicate,
                'claim_type': ast.claim_type
            }
        })
        
    elements = nodes + edges
    
    return render(request, 'research/network_explorer.html', {
        'elements_json': json.dumps(elements)
    })

def compare_entities(request):
    from apps.entities.models import Entity
    from apps.assertions.models import Assertion
    from django.db.models import Q
    
    entity_a_id = request.GET.get('entity_a')
    entity_b_id = request.GET.get('entity_b')
    
    entities = Entity.objects.exclude(status='MERGED').order_by('canonical_name')
    
    entity_a = Entity.objects.filter(id=entity_a_id).first() if entity_a_id else None
    entity_b = Entity.objects.filter(id=entity_b_id).first() if entity_b_id else None
    
    direct_assertions = []
    shared_neighbors = []
    
    if entity_a and entity_b:
        # Find direct assertions
        direct_assertions = Assertion.objects.filter(
            Q(subject_entity=entity_a, object_entity=entity_b) |
            Q(subject_entity=entity_b, object_entity=entity_a)
        )
        
        # Find neighbors A
        neighbors_a = set()
        for ast in Assertion.objects.filter(subject_entity=entity_a, object_entity__isnull=False):
            neighbors_a.add(ast.object_entity)
        for ast in Assertion.objects.filter(object_entity=entity_a):
            neighbors_a.add(ast.subject_entity)
            
        # Find neighbors B
        neighbors_b = set()
        for ast in Assertion.objects.filter(subject_entity=entity_b, object_entity__isnull=False):
            neighbors_b.add(ast.object_entity)
        for ast in Assertion.objects.filter(object_entity=entity_b):
            neighbors_b.add(ast.subject_entity)
            
        shared_neighbors = list(neighbors_a.intersection(neighbors_b))
        
    return render(request, 'research/compare_entities.html', {
        'entities': entities,
        'entity_a': entity_a,
        'entity_b': entity_b,
        'direct_assertions': direct_assertions,
        'shared_neighbors': shared_neighbors
    })
