import pytest
from django.test import Client
from apps.entities.models import Entity
from apps.research.models import ResearchCollection

@pytest.mark.django_db
def test_pin_entity_to_collection_via_form():
    client = Client()
    
    # 1. Setup Entity and Research Collection
    entity = Entity.objects.create(
        public_id="ENT_PIN_1",
        canonical_name="Test Pin Entity",
        entity_type="PERSON"
    )
    col = ResearchCollection.objects.create(
        name="Pin Collection Target",
        description="Workspace for pinning tests"
    )
    
    # 2. Check entity detail view context includes all_collections
    response = client.get(f'/entity/{entity.public_id}/')
    assert response.status_code == 200
    assert 'all_collections' in response.context
    
    # 3. Post to generic add_item_to_collection route
    post_response = client.post('/research/collections/add-item/', {
        'collection_id': str(col.id),
        'item_type': 'entity',
        'item_id': str(entity.id)
    })
    
    assert post_response.status_code == 302
    
    # 4. Verify entity was pinned to the collection
    assert col.entities.filter(id=entity.id).exists()
