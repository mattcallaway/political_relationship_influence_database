from django.shortcuts import render, get_object_or_404
from apps.campaigns.models import Campaign
from apps.entities.models import Entity
from apps.transactions.models import Contribution, Expenditure
from apps.assertions.models import Assertion
from apps.research.models import ResearchCollection

def campaign_detail(request, public_id):
    campaign = get_object_or_404(Campaign, public_id=public_id)
    
    # Paying committee
    committee_entity = campaign.committee
    
    # Donors
    donors = []
    expenditures = []
    treasurer = None
    
    if committee_entity:
        donors = Contribution.objects.filter(filer_committee=committee_entity).select_related('donor_entity').order_by('-amount')
        expenditures = Expenditure.objects.filter(filer_committee=committee_entity).select_related('payee_entity').order_by('-amount')
        
        # Get treasurer from profile
        committee_profile = getattr(committee_entity, 'committee_profile', None)
        if committee_profile and committee_profile.treasurer_name:
            treasurer = committee_profile.treasurer_name
            
    # If no treasurer string, check for TREASURER_FOR assertions
    if not treasurer and committee_entity:
        treasurer_assertion = Assertion.objects.filter(object_entity=committee_entity, predicate='TREASURER_FOR').first()
        if treasurer_assertion:
            treasurer = treasurer_assertion.subject_entity.canonical_name

    # Consultants
    # Look for both assertions and expenditures with CNS code / role
    consultants_set = set()
    
    # 1. Assertions
    consultant_assertions = Assertion.objects.filter(
        object_entity=campaign.entity,
        predicate__in=['CONSULTANT_TO', 'CAMPAIGN_MANAGER_FOR']
    ).select_related('subject_entity')
    for ast in consultant_assertions:
        consultants_set.add((ast.subject_entity, ast.predicate))
        
    # 2. Expenditures with consultant code or role
    if committee_entity:
        consultant_exps = Expenditure.objects.filter(
            filer_committee=committee_entity,
            transaction_code='CNS'
        ).select_related('payee_entity')
        for exp in consultant_exps:
            if exp.payee_entity:
                consultants_set.add((exp.payee_entity, 'CONSULTANT_TO'))

    # Source documents
    sources = set()
    for con in donors:
        if con.source:
            sources.add(con.source)
    for exp in expenditures:
        if exp.source:
            sources.add(exp.source)
            
    # Related campaigns (same candidate or same office)
    related_campaigns = []
    if campaign.candidate:
        related_campaigns = Campaign.objects.filter(candidate=campaign.candidate).exclude(id=campaign.id)

    # Collections
    all_collections = ResearchCollection.objects.all()

    # Targeted Independent Expenditures (Form 496)
    independent_expenditures = Expenditure.objects.filter(
        campaign=campaign,
        is_independent_expenditure=True
    ).select_related('filer_committee', 'payee_entity').order_by('-amount')
    
    support_expenditures = [ie for ie in independent_expenditures if ie.support_oppose == 'SUPPORT']
    oppose_expenditures = [ie for ie in independent_expenditures if ie.support_oppose == 'OPPOSE']

    return render(request, 'campaigns/campaign_detail.html', {
        'campaign': campaign,
        'committee_entity': committee_entity,
        'donors': donors[:100],
        'expenditures': expenditures[:100],
        'treasurer': treasurer,
        'consultants': list(consultants_set),
        'sources': list(sources),
        'related_campaigns': related_campaigns,
        'all_collections': all_collections,
        'support_expenditures': support_expenditures,
        'oppose_expenditures': oppose_expenditures
    })
