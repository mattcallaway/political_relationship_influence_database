import pytest
import uuid
from django.test import Client
from apps.entities.models import Entity, EntityStatus, PublicationStatus
from apps.assertions.models import Assertion, VerificationStatus
from apps.transactions.models import Contribution, AuditEvent

@pytest.mark.django_db
def test_entity_moderation_view_and_audit():
    client = Client()
    ent = Entity.objects.create(
        public_id='ENT_MOD_1',
        canonical_name='Modifiable Entity',
        entity_type='PERSON',
        status=EntityStatus.PROPOSED,
        publication_status=PublicationStatus.INTERNAL_ONLY
    )
    
    # Post updates
    response = client.post(f'/entity/{ent.public_id}/moderate/', {
        'status': 'VERIFIED',
        'publication_status': 'PUBLISHED'
    })
    
    # Reload and assert status changes
    ent.refresh_from_db()
    assert ent.status == 'VERIFIED'
    assert ent.publication_status == 'PUBLISHED'
    assert response.status_code == 302
    
    # Verify AuditEvent logging
    audit = AuditEvent.objects.filter(record_id=str(ent.id), action="MODERATE").first()
    assert audit is not None
    assert audit.new_value.get('status') == 'VERIFIED'

@pytest.mark.django_db
def test_assertion_moderation_view_and_audit():
    client = Client()
    subject = Entity.objects.create(public_id='ENT_SUB_1', canonical_name='Sub', entity_type='PERSON')
    ast = Assertion.objects.create(
        public_id='AST-MOD-1',
        subject_entity=subject,
        predicate='EMPLOYEE_OF',
        object_value='Corp',
        verification_status='PROPOSED'
    )
    
    response = client.post(f'/assertions/moderate/{ast.id}/', {
        'verification_status': 'VERIFIED'
    })
    
    ast.refresh_from_db()
    assert ast.verification_status == 'VERIFIED'
    assert response.status_code == 302
    
    # Verify AuditEvent logging
    audit = AuditEvent.objects.filter(record_id=str(ast.id), action="MODERATE").first()
    assert audit is not None
    assert audit.new_value.get('verification_status') == 'VERIFIED'

@pytest.mark.django_db
def test_quick_moderation_bulk_action():
    client = Client()
    ent = Entity.objects.create(
        public_id='ENT_PROV_1',
        canonical_name='Provisional Entity',
        entity_type='PERSON',
        status=EntityStatus.PROVISIONAL_AUTO_CREATED
    )
    
    # Verify via review queue bulk action
    response = client.post('/extraction/moderate/bulk/', {
        'action': 'verify',
        'record_type': 'entity',
        'record_id': str(ent.id)
    })
    
    ent.refresh_from_db()
    assert ent.status == 'VERIFIED'
    assert response.status_code == 302
