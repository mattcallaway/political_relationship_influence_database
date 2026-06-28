import pytest
from django.core.management import call_command
from apps.entities.models import Entity, Person, Organization
from apps.sources.models import Source
from apps.documents.models import Document

@pytest.mark.django_db
def test_v5_workbook_import_idempotency():
    # Run import first time
    call_command('import_v5_workbook')
    entity_count_1 = Entity.objects.count()
    source_count_1 = Source.objects.count()
    assert entity_count_1 > 0
    assert source_count_1 > 0

    # Run import second time (idempotency check)
    call_command('import_v5_workbook')
    entity_count_2 = Entity.objects.count()
    source_count_2 = Source.objects.count()
    assert entity_count_1 == entity_count_2
    assert source_count_1 == source_count_2

@pytest.mark.django_db
def test_canonical_entity_creation():
    e = Entity.objects.create(public_id='P999999', canonical_name='Test Researcher', entity_type='PERSON')
    Person.objects.create(entity=e, display_name='Test Researcher')
    assert e.person_profile.display_name == 'Test Researcher'
