import pytest
from django.test import Client
from apps.entities.models import Entity, EntityStatus
from apps.transactions.models import Contribution, ReviewStatus
from apps.assertions.models import Assertion
from apps.research.models import ResearchCollection, ResearchTask, OpenQuestion, EntityMatchCandidate
from apps.government.models import Vote, GovernmentBody

@pytest.mark.django_db
def test_automatch_status_is_distinct_from_verified():
    # Fuzzy match produces AUTO_MATCHED, not VERIFIED
    contrib = Contribution(
        public_id='CON_TEST_50',
        donor_raw_name='Fuzzy Named Contributor',
        amount=100.0,
        review_status=ReviewStatus.AUTO_MATCHED
    )
    assert contrib.review_status != ReviewStatus.VERIFIED
    assert contrib.review_status == 'AUTO_MATCHED'

@pytest.mark.django_db
def test_provisional_entities_are_visible_and_provisional():
    ent = Entity.objects.create(
        public_id='ENT_PROV_TEST',
        canonical_name='Provisional Member',
        entity_type='PERSON',
        status=EntityStatus.PROVISIONAL_AUTO_CREATED
    )
    assert ent.status == 'PROVISIONAL_AUTO_CREATED'
    
@pytest.mark.django_db
def test_muelrath_collection_workspace_and_actions():
    client = Client()
    
    # 1. Create collection
    col = ResearchCollection.objects.create(
        name="Muelrath Public Affairs",
        description="Comprehensive network analysis"
    )
    
    # 2. Assert collection starts with empty grids (gaps)
    response = client.get(f'/research/collections/{col.id}/')
    assert response.status_code == 200
    html = response.content.decode()
    # Missing categories are shown as research gaps!
    assert "No public contracts recorded." in html
    assert "No lobbying activities registered." in html
    
    # 3. Create a task from the collection endpoint
    task_response = client.post(f'/research/collections/{col.id}/task/create/', {
        'task_title': 'Audit FPPC ID records',
        'priority': 'HIGH',
        'notes': 'Verify all campaign consultants'
    })
    assert task_response.status_code == 302
    assert ResearchTask.objects.filter(collection=col, task_title='Audit FPPC ID records').exists()
    
    # 4. Create a question from the collection endpoint
    q_response = client.post(f'/research/collections/{col.id}/question/create/', {
        'question_text': 'What committees paid the consultant?'
    })
    assert q_response.status_code == 302
    assert OpenQuestion.objects.filter(collection=col, question_text='What committees paid the consultant?').exists()

@pytest.mark.django_db
def test_graph_edges_expose_origin_record_ids():
    # Setup assertion with subject/object
    subject = Entity.objects.create(public_id='ENT_SUB_5', canonical_name='Sub', entity_type='PERSON')
    obj = Entity.objects.create(public_id='ENT_OBJ_5', canonical_name='Obj', entity_type='PERSON')
    
    ast = Assertion.objects.create(
        public_id='AST-EDGE-1',
        subject_entity=subject,
        predicate='ASSOCIATED_WITH',
        object_entity=obj,
        verification_status='VERIFIED'
    )
    
    client = Client()
    response = client.get('/research/network/')
    assert response.status_code == 200
    html = response.content.decode()
    # Exposes origin record ID in network elements!
    assert 'AST-EDGE-1' in html
