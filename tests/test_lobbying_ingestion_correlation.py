import pytest
from decimal import Decimal
from django.test import Client
from apps.entities.models import Entity
from apps.campaigns.models import Campaign, Committee
from apps.transactions.models import Contribution, Expenditure, LobbyingActivity
from apps.documents.models import Document, DocumentPage
from apps.sources.models import Source
from apps.assertions.models import Assertion
from apps.extraction.generic_parsers import parse_lobbying_disclosure

@pytest.mark.django_db
def test_parse_lobbying_disclosure_and_client_relation():
    src = Source.objects.create(public_id="SRC_LOB_TEST", title="Lobbying Report Q3 2026")
    doc = Document.objects.create(original_filename="lobbying_report.pdf", source=src)
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="""
        QUARTERLY LOBBYING DISCLOSURE
        Lobbyist: Muelrath Public Affairs
        Client: Sonoma County Land Developer Association
        Agency: Sonoma County Board of Supervisors
        Period: Q3 2026
        Compensation: 7500.00
        Matters: Lobbying on zoning amendments and permits
        """
    )
    
    parse_lobbying_disclosure(doc, src)
    
    # Assert lobbying activity created
    lob = LobbyingActivity.objects.filter(reporting_period="Q3 2026").first()
    assert lob is not None
    assert lob.compensation_amount == Decimal("7500.00")
    assert lob.lobbyist_entity.canonical_name == "Muelrath Public Affairs"
    assert lob.client_entity.canonical_name == "Sonoma County Land Developer Association"
    
    # Assert CLIENT_OF assertion exists
    assert Assertion.objects.filter(
        subject_entity=lob.lobbyist_entity,
        object_entity=lob.client_entity,
        predicate='CLIENT_OF'
    ).exists()

@pytest.mark.django_db
def test_lobbying_and_campaign_intersection_panel():
    client = Client()
    
    # 1. Setup firm entity
    firm_ent = Entity.objects.create(
        public_id="ENT_FIRM_99",
        canonical_name="Muelrath Public Affairs",
        entity_type="ORGANIZATION"
    )
    
    # 2. Setup client entity & lobbying activity
    client_ent = Entity.objects.create(
        public_id="ENT_CLIENT_99",
        canonical_name="Bellevue Real Estate Corp",
        entity_type="ORGANIZATION"
    )
    agency_ent = Entity.objects.create(
        public_id="ENT_AGEN_99",
        canonical_name="Sonoma County Board of Supervisors",
        entity_type="GOVERNMENT_BODY"
    )
    
    LobbyingActivity.objects.create(
        public_id="LOB_99",
        lobbyist_entity=firm_ent,
        client_entity=client_ent,
        agency_entity=agency_ent,
        reporting_period="Q1 2026",
        compensation_amount=5000.00
    )
    
    # 3. Setup campaign and consultant expenditure
    candidate = Entity.objects.create(
        public_id="ENT_CAND_99",
        canonical_name="James Gore",
        entity_type="PERSON"
    )
    committee_entity = Entity.objects.create(
        public_id="ENT_COMM_99",
        canonical_name="James Gore for Supervisor 2026",
        entity_type="COMMITTEE"
    )
    campaign = Campaign.objects.create(
        public_id="CAMP_99",
        campaign_name="James Gore for Supervisor 2026",
        election_year=2026,
        candidate=candidate,
        committee=committee_entity
    )
    
    Expenditure.objects.create(
        public_id="EXP_99",
        filer_committee=committee_entity,
        payee_entity=firm_ent,
        payee_raw_name="Muelrath Public Affairs",
        amount=1500.00,
        transaction_code="CNS",
        campaign=campaign
    )
    
    # 4. View firm details
    response = client.get(f'/entity/{firm_ent.public_id}/')
    assert response.status_code == 200
    
    # Verify both lobbying activities and campaigns are populated in context
    assert len(response.context['lobbying_as_firm']) == 1
    assert len(response.context['consultant_campaigns']) == 1
