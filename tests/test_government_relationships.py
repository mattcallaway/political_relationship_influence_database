import pytest
from django.test import Client
import datetime
from apps.entities.models import Entity
from apps.government.models import GovernmentBody, Meeting, Appointment

@pytest.mark.django_db
def test_government_body_meetings_detail_view():
    client = Client()
    
    # 1. Create a Government Body Entity and Profile
    body_entity = Entity.objects.create(
        public_id="ENT_GOV_BODY_1",
        canonical_name="County Board of Supervisors",
        entity_type="GOVERNMENT_BODY"
    )
    gov_body = GovernmentBody.objects.create(
        public_id="GOV_BODY_1",
        entity=body_entity,
        body_name="County Board of Supervisors"
    )
    
    # 2. Create a Meeting held by this body
    meeting = Meeting.objects.create(
        government_body=gov_body,
        date=datetime.date(2026, 6, 15),
        location="County Center"
    )
    
    # 3. Create a person Entity and Appointment to this body
    person_entity = Entity.objects.create(
        public_id="ENT_PERSON_APT_1",
        canonical_name="Jane Doe",
        entity_type="PERSON"
    )
    appointer_entity = Entity.objects.create(
        public_id="ENT_APPOINTER_1",
        canonical_name="Board Chair",
        entity_type="PERSON"
    )
    
    apt = Appointment.objects.create(
        public_id="APT_1",
        person_entity=person_entity,
        body_entity=body_entity,
        appointer_entity=appointer_entity,
        start_date=datetime.date(2025, 1, 1),
        position_title="District 1 Supervisor"
    )
    
    # 4. Fetch detail view for person (should include appointment & appointer details)
    response_person = client.get(f'/entity/{person_entity.public_id}/')
    assert response_person.status_code == 200
    assert 'appointments' in response_person.context
    appointments_list = list(response_person.context['appointments'])
    assert len(appointments_list) == 1
    assert appointments_list[0].position_title == "District 1 Supervisor"
    assert appointments_list[0].appointer_entity == appointer_entity
    
    # 5. Fetch detail view for government body (should include body profile & meetings)
    response_body = client.get(f'/entity/{body_entity.public_id}/')
    assert response_body.status_code == 200
    assert response_body.context['body_profile'] == gov_body
    assert len(response_body.context['meetings']) == 1
