import pytest
from django.test import Client
import datetime
import json
from apps.entities.models import Entity
from apps.assertions.models import Assertion
from apps.transactions.models import Contribution

@pytest.mark.django_db
def test_network_explorer_multidimensional_edges():
    client = Client()
    
    # Setup some entities
    ent_a = Entity.objects.create(public_id="ENT_NET_A", canonical_name="Node A", entity_type="PERSON")
    ent_b = Entity.objects.create(public_id="ENT_NET_B", canonical_name="Node B", entity_type="ORGANIZATION")
    
    # 1. Create a Contribution
    Contribution.objects.create(
        public_id="CON_NET_1",
        filer_committee=ent_b,
        donor_entity=ent_a,
        donor_raw_name="Node A",
        amount=100.0
    )
    
    # 2. Create an Assertion
    Assertion.objects.create(
        public_id="AST_NET_1",
        subject_entity=ent_a,
        object_entity=ent_b,
        predicate="employed_by"
    )
    
    response = client.get('/research/network/')
    assert response.status_code == 200
    assert 'elements_json' in response.context
    
    # Verify that the compiled JSON elements contain both edges
    elements_str = response.context['elements_json']
    assert "CON_NET_1" in elements_str
    assert "AST_NET_1" in elements_str
    assert "Node A" in elements_str

@pytest.mark.django_db
def test_compare_entities_chronological_overlapping_timeline():
    client = Client()
    
    ent_a = Entity.objects.create(public_id="ENT_COMP_A", canonical_name="Compare A", entity_type="PERSON")
    ent_b = Entity.objects.create(public_id="ENT_COMP_B", canonical_name="Compare B", entity_type="COMMITTEE")
    
    # Create contribution involving either
    Contribution.objects.create(
        public_id="CON_COMP_1",
        filer_committee=ent_b,
        donor_entity=ent_a,
        donor_raw_name="Compare A",
        amount=500.0,
        transaction_date=datetime.date(2026, 5, 20)
    )
    
    response = client.get(f'/research/compare/?entity_a={ent_a.id}&entity_b={ent_b.id}')
    assert response.status_code == 200
    assert 'timeline' in response.context
    
    timeline_list = response.context['timeline']
    assert len(timeline_list) == 1
    assert timeline_list[0]['type'] == 'Contribution'
    assert timeline_list[0]['actor'] == 'Entity A'
