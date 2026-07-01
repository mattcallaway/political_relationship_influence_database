import pytest
from django.test import Client

@pytest.mark.django_db
def test_methodology_page_view():
    client = Client()
    response = client.get('/research/methodology/')
    assert response.status_code == 200
    assert b"Research Methodology" in response.content
    assert b"Strict Evidence Provenance" in response.content
    assert b"Non-Pejorative Stance" in response.content
