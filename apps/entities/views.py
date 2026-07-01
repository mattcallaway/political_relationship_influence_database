from django.shortcuts import render, get_object_or_404
from apps.entities.models import Entity, Person, Organization

def entity_list(request):
    query = request.GET.get('q', '')
    etype = request.GET.get('type', '')
    status = request.GET.get('status', '')
    exclude_rejected = request.GET.get('exclude_rejected', 'false') == 'true'
    show_duplicates = request.GET.get('show_duplicates', 'false') == 'true'
    directory = request.GET.get('dir', 'all')
    sort_field = request.GET.get('sort', 'public_id')
    
    sort_mapping = {
        'name': 'canonical_name',
        'type': 'entity_type',
        'status': 'status',
        'jurisdiction': 'jurisdiction',
        'date_added': 'created_at',
        'date_updated': '-updated_at',
        'public_id': 'public_id'
    }
    order_by_field = sort_mapping.get(sort_field, 'public_id')
    
    entities = Entity.objects.all()
    
    # Directory filter
    if directory == 'provisional':
        from apps.entities.models import EntityStatus
        entities = entities.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED)
    elif directory == 'possible_duplicates':
        show_duplicates = True
    elif directory == 'recent':
        order_by_field = '-updated_at'
    elif directory in ['PERSON', 'ORGANIZATION', 'CAMPAIGN', 'COMMITTEE', 'DEVELOPMENT_PROJECT', 'GOVERNMENT_BODY', 'PUBLIC_OFFICE', 'BALLOT_MEASURE', 'PROPERTY_OR_SITE', 'CONTRACT', 'EVENT']:
        entities = entities.filter(entity_type=directory)
        
    if exclude_rejected:
        from apps.entities.models import EntityStatus
        entities = entities.exclude(status=EntityStatus.REJECTED)
        
    if status == 'verified_only':
        from apps.entities.models import EntityStatus
        entities = entities.filter(status=EntityStatus.VERIFIED)
    elif status == 'reviewed':
        from apps.entities.models import EntityStatus
        entities = entities.filter(status__in=[EntityStatus.REVIEWED, EntityStatus.VERIFIED])
    elif status == 'auto-matched':
        from apps.entities.models import EntityStatus
        entities = entities.filter(status=EntityStatus.AUTO_MATCHED)
    elif status == 'provisional':
        from apps.entities.models import EntityStatus
        entities = entities.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED)
        
    if show_duplicates:
        from django.db.models import Count
        duplicate_names = Entity.objects.values('canonical_name').annotate(name_count=Count('id')).filter(name_count__gt=1)
        names_list = [d['canonical_name'] for d in duplicate_names]
        entities = entities.filter(canonical_name__in=names_list)
        
    if query:
        from django.db.models import Q
        from apps.entities.models import Alias
        from apps.campaigns.models import Campaign, Committee
        from apps.entities.models import Project as ProjectSubtype
        
        q_entities = Q(canonical_name__icontains=query)
        
        matching_aliases = Alias.objects.filter(alias_text__icontains=query).values_list('entity_id', flat=True)
        q_aliases = Q(id__in=matching_aliases)
        
        matching_committees = Committee.objects.filter(fppc_id__icontains=query).values_list('entity_id', flat=True)
        q_committees = Q(id__in=matching_committees)

        matching_campaigns = Campaign.objects.filter(campaign_name__icontains=query).values_list('entity_id', flat=True)
        q_campaigns = Q(id__in=matching_campaigns)

        matching_projects = ProjectSubtype.objects.filter(project_category__icontains=query).values_list('entity_id', flat=True)
        q_projects = Q(id__in=matching_projects)

        entities = entities.filter(q_entities | q_aliases | q_committees | q_campaigns | q_projects)
        
    if etype:
        entities = entities.filter(entity_type=etype)
        
    entities = entities.order_by(order_by_field)
        
    return render(request, 'entities/entity_list.html', {
        'entities': entities[:100],
        'query': query,
        'selected_type': etype,
        'selected_status': status,
        'exclude_rejected': exclude_rejected,
        'show_duplicates': show_duplicates,
        'selected_dir': directory,
        'selected_sort': sort_field
    })

def entity_detail(request, public_id):
    entity = get_object_or_404(Entity, public_id=public_id)
    person = Person.objects.filter(entity=entity).first()
    org = Organization.objects.filter(entity=entity).first()
    
    subject_assertions = entity.subject_assertions.all()
    object_assertions = entity.object_assertions.all()
    
    contributions_received = entity.contributions_received.all()
    contributions_made = entity.contributions_made.all()
    
    # Expanded relations lookup
    expenditures_made = entity.expenditures_made.all() if hasattr(entity, 'expenditures_made') else []
    expenditures_received = entity.expenditures_received.all() if hasattr(entity, 'expenditures_received') else []
    
    appointments = entity.appointments.all() if hasattr(entity, 'appointments') else []
    made_appointments = entity.made_appointments.all() if hasattr(entity, 'made_appointments') else []
    
    vendor_contracts = entity.vendor_contracts.all() if hasattr(entity, 'vendor_contracts') else []
    agency_contracts = entity.agency_contracts.all() if hasattr(entity, 'agency_contracts') else []
    
    lobbying_as_firm = entity.lobbying_as_firm.all() if hasattr(entity, 'lobbying_as_firm') else []
    lobbying_as_client = entity.lobbying_as_client.all() if hasattr(entity, 'lobbying_as_client') else []
    
    votes_cast = entity.votes_cast.all() if hasattr(entity, 'votes_cast') else []
    
    # Subtype queries
    campaigns = []
    if entity.entity_type == 'CAMPAIGN' and hasattr(entity, 'campaign_profile'):
        campaigns = [entity.campaign_profile]
    
    projects = []
    if hasattr(entity, 'project_profile'):
        projects = [entity.project_profile]
        
    aliases = entity.aliases.all()
    
    # Build timeline feed
    timeline = []
    
    for c in contributions_made:
        if c.transaction_date:
            timeline.append({
                'date': c.transaction_date,
                'type': 'Contribution Made',
                'description': f"Contributed ${c.amount} to {c.filer_committee.canonical_name}",
                'amount': c.amount
            })
            
    for c in contributions_received:
        if c.transaction_date:
            timeline.append({
                'date': c.transaction_date,
                'type': 'Contribution Received',
                'description': f"Received ${c.amount} from {c.donor_raw_name}",
                'amount': c.amount
            })

    for e in expenditures_made:
        if e.transaction_date:
            timeline.append({
                'date': e.transaction_date,
                'type': 'Expenditure Made',
                'description': f"Spent ${e.amount} paid to {e.payee_raw_name} ({e.description or e.purpose_code})",
                'amount': e.amount
            })

    for a in appointments:
        if a.start_date:
            timeline.append({
                'date': a.start_date,
                'type': 'Appointment Start',
                'description': f"Appointed to body: {a.body_entity.canonical_name}"
            })
        if a.end_date:
            timeline.append({
                'date': a.end_date,
                'type': 'Appointment End',
                'description': f"Term completed on body: {a.body_entity.canonical_name}"
            })

    for ctr in vendor_contracts:
        if ctr.execution_date:
            timeline.append({
                'date': ctr.execution_date,
                'type': 'Contract Received',
                'description': f"Contract executed with agency {ctr.agency_entity.canonical_name}: {ctr.contract_title}",
                'amount': ctr.amount
            })

    for v in votes_cast:
        if v.meeting_date:
            timeline.append({
                'date': v.meeting_date,
                'type': 'Vote Cast',
                'description': f"Voted {v.vote_cast} on agenda item: {v.item_title}"
            })

    for ast in subject_assertions:
        if ast.effective_start:
            timeline.append({
                'date': ast.effective_start,
                'type': 'Relationship Start',
                'description': f"Relationship start: {ast.subject_entity.canonical_name} [{ast.predicate}] " + (ast.object_entity.canonical_name if ast.object_entity else ast.object_value)
            })

    # Sort timeline descending
    timeline.sort(key=lambda x: x['date'] or datetime.date.today(), reverse=True)
    
    return render(request, 'entities/entity_detail.html', {
        'entity': entity,
        'person': person,
        'org': org,
        'aliases': aliases,
        'subject_assertions': subject_assertions,
        'object_assertions': object_assertions,
        'contributions_received': contributions_received,
        'contributions_made': contributions_made,
        'expenditures_made': expenditures_made,
        'expenditures_received': expenditures_received,
        'appointments': appointments,
        'made_appointments': made_appointments,
        'vendor_contracts': vendor_contracts,
        'agency_contracts': agency_contracts,
        'lobbying_as_firm': lobbying_as_firm,
        'lobbying_as_client': lobbying_as_client,
        'votes_cast': votes_cast,
        'campaigns': campaigns,
        'projects': projects,
        'timeline': timeline
    })

def unified_search(request):
    from django.db.models import Q
    from apps.entities.models import Entity, Alias
    from apps.documents.models import Document
    from apps.assertions.models import Assertion
    from apps.transactions.models import Contribution, LobbyingActivity, Contract
    from apps.government.models import Meeting, Vote
    from apps.research.models import SavedSearch
    
    q = request.GET.get('q', '').strip()
    save_search = request.GET.get('save_search', '') == 'true'
    
    results = {}
    saved_searches = SavedSearch.objects.all().order_by('-created_at')[:10]
    
    if q:
        # Save Search if requested
        if save_search:
            SavedSearch.objects.get_or_create(
                name=f"Search for '{q}'",
                query_string=q
            )
            
        # 1. Entities
        results['entities'] = Entity.objects.filter(
            Q(canonical_name__icontains=q) |
            Q(aliases__alias_text__icontains=q)
        ).distinct()[:20]
        
        # 2. Documents
        results['documents'] = Document.objects.filter(
            Q(original_filename__icontains=q) |
            Q(pages__extracted_text__icontains=q) |
            Q(pages__ocr_text__icontains=q)
        ).distinct()[:20]
        
        # 3. Assertions
        results['assertions'] = Assertion.objects.filter(
            Q(predicate__icontains=q) |
            Q(explanatory_note__icontains=q) |
            Q(object_value__icontains=q)
        ).distinct()[:20]

        # 4. Transactions
        results['contributions'] = Contribution.objects.filter(
            Q(donor_raw_name__icontains=q) |
            Q(donor_entity__canonical_name__icontains=q) |
            Q(filer_committee__canonical_name__icontains=q)
        ).distinct()[:20]

        # 5. Lobbying
        results['lobbying'] = LobbyingActivity.objects.filter(
            Q(lobbyist_entity__canonical_name__icontains=q) |
            Q(client_entity__canonical_name__icontains=q) |
            Q(matters_described__icontains=q)
        ).distinct()[:20]

        # 6. Contracts
        results['contracts'] = Contract.objects.filter(
            Q(contract_title__icontains=q) |
            Q(agency_entity__canonical_name__icontains=q) |
            Q(vendor_entity__canonical_name__icontains=q)
        ).distinct()[:20]

        # 7. Meetings & Votes
        results['meetings'] = Meeting.objects.filter(
            Q(location__icontains=q) |
            Q(agenda_items__title__icontains=q) |
            Q(agenda_items__description__icontains=q)
        ).distinct()[:20]
        
        results['votes'] = Vote.objects.filter(
            Q(item_title__icontains=q) |
            Q(voter_person__canonical_name__icontains=q)
        ).distinct()[:20]

    return render(request, 'entities/search_results.html', {
        'query': q,
        'results': results,
        'saved_searches': saved_searches
    })
