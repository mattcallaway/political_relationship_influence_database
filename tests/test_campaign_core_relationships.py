import pytest
from django.test import Client
import datetime
from apps.entities.models import Entity
from apps.campaigns.models import Campaign, Committee
from apps.transactions.models import Contribution, Expenditure

@pytest.mark.django_db
def test_campaign_detail_and_expenditure_fields():
    client = Client()
    
    # 1. Create candidate, campaign, and committee
    candidate = Entity.objects.create(
        public_id="ENT_CAND_1",
        canonical_name="John Candidate",
        entity_type="PERSON"
    )
    committee_entity = Entity.objects.create(
        public_id="ENT_COMM_1",
        canonical_name="John for Council 2026",
        entity_type="COMMITTEE"
    )
    committee_profile = Committee.objects.create(
        public_id="COMM_1",
        entity=committee_entity,
        committee_name="John for Council 2026",
        treasurer_name="Jane Treasurer"
    )
    campaign = Campaign.objects.create(
        public_id="CAMP_1",
        campaign_name="John Candidate 2026",
        election_year=2026,
        candidate=candidate,
        committee=committee_entity
    )
    
    # 2. Create payee/vendor
    payee = Entity.objects.create(
        public_id="ENT_VEND_1",
        canonical_name="Media Consultant LLC",
        entity_type="ORGANIZATION"
    )
    
    # 3. Create expenditure linking all fields
    exp = Expenditure.objects.create(
        public_id="EXP_1",
        filer_committee=committee_entity,
        payee_entity=payee,
        payee_raw_name="Media Consultant LLC",
        amount=1200.00,
        transaction_code="CNS",
        campaign=campaign,
        consultant_vendor_role="CNS_STRATEGY",
        source_page=4
    )
    
    # 4. Fetch Campaign Detail View
    response = client.get(f'/campaigns/{campaign.public_id}/')
    assert response.status_code == 200
    assert response.context['campaign'] == campaign
    assert response.context['committee_entity'] == committee_entity
    assert response.context['treasurer'] == "Jane Treasurer"
    assert len(response.context['consultants']) == 1
    assert len(response.context['expenditures']) == 1

@pytest.mark.django_db
def test_shared_connections_view():
    client = Client()
    
    # Setup shared infrastructure
    comm_a = Entity.objects.create(public_id="ENT_C_A", canonical_name="Committee A", entity_type="COMMITTEE")
    comm_b = Entity.objects.create(public_id="ENT_C_B", canonical_name="Committee B", entity_type="COMMITTEE")
    
    camp_a = Campaign.objects.create(public_id="CAMP_A", campaign_name="Campaign A", election_year=2026, committee=comm_a)
    camp_b = Campaign.objects.create(public_id="CAMP_B", campaign_name="Campaign B", election_year=2026, committee=comm_b)
    
    shared_payee = Entity.objects.create(public_id="ENT_SHARED_1", canonical_name="Shared Agency", entity_type="ORGANIZATION")
    
    Expenditure.objects.create(
        public_id="EXP_A", filer_committee=comm_a, payee_entity=shared_payee, payee_raw_name="Shared Agency", amount=500, transaction_code="CNS"
    )
    Expenditure.objects.create(
        public_id="EXP_B", filer_committee=comm_b, payee_entity=shared_payee, payee_raw_name="Shared Agency", amount=800, transaction_code="CNS"
    )
    
    response = client.get('/research/shared-connections/')
    assert response.status_code == 200
    assert 'consultant_groups' in response.context
    groups = response.context['consultant_groups']
    assert len(groups) >= 1
    assert groups[0]['consultant_name'] == "Shared Agency"
    assert len(groups[0]['campaigns']) == 2

@pytest.mark.django_db
def test_data_quality_diagnostics():
    client = Client()
    
    # Create orphan/unlinked payee expenditure
    comm = Entity.objects.create(public_id="ENT_COMM_X", canonical_name="Committee X", entity_type="COMMITTEE")
    Expenditure.objects.create(
        public_id="EXP_UNLINKED", filer_committee=comm, payee_raw_name="Unlinked Vendor", amount=150.00
    )
    
    response = client.get('/research/data-quality/')
    assert response.status_code == 200
    assert 'issues' in response.context
    issues = response.context['issues']
    
    # Check that Payee Missing Entity Link was flagged
    missing_link_issues = [i for i in issues if i.issue_type == "Payee Missing Entity Link"]
    assert len(missing_link_issues) >= 1
