from django.shortcuts import render, get_object_or_404
from apps.entities.models import Entity, Person, Organization

def entity_list(request):
    query = request.GET.get('q', '')
    etype = request.GET.get('type', '')
    
    entities = Entity.objects.all().order_by('public_id')
    if query:
        entities = entities.filter(canonical_name__icontains=query)
    if etype:
        entities = entities.filter(entity_type=etype)
        
    return render(request, 'entities/entity_list.html', {
        'entities': entities[:50],
        'query': query,
        'selected_type': etype
    })

def entity_detail(request, public_id):
    entity = get_object_or_404(Entity, public_id=public_id)
    person = Person.objects.filter(entity=entity).first()
    org = Organization.objects.filter(entity=entity).first()
    
    subject_assertions = entity.subject_assertions.all()
    object_assertions = entity.object_assertions.all()
    
    contributions_received = entity.contributions_received.all()
    contributions_made = entity.contributions_made.all()
    
    return render(request, 'entities/entity_detail.html', {
        'entity': entity,
        'person': person,
        'org': org,
        'subject_assertions': subject_assertions,
        'object_assertions': object_assertions,
        'contributions_received': contributions_received,
        'contributions_made': contributions_made
    })
