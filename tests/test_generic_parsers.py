import pytest
from django.contrib.auth import get_user_model
from apps.entities.models import Entity, EntityType
from apps.documents.models import Document, DocumentPage
from apps.sources.models import Source
from apps.government.models import Meeting, AgendaItem, Motion, Vote
from apps.transactions.models import LobbyingActivity
from apps.extraction.generic_parsers import generic_document_ingestion

User = get_user_model()

@pytest.mark.django_db
def test_meeting_minutes_ingestion():
    # Setup test document
    doc = Document.objects.create(
        original_filename="minutes_test.pdf",
        sha256_hash="dummy_hash_minutes"
    )
    
    # Page text containing minutes keywords
    page_text = """
    BOARD OF SUPERVISORS MEETING MINUTES
    January 15, 2026
    Item 1: Approve Bellevue School District application.
    Moved by Supervisor Gore, seconded by Supervisor Carrillo. Passed 5-0.
    """
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text=page_text
    )
    
    # Run Ingestion
    generic_document_ingestion(doc)
    
    # Assert Meeting was created
    meeting = Meeting.objects.first()
    assert meeting is not None
    assert meeting.date.year == 2026
    
    # Assert Agenda Item and Motion
    item = AgendaItem.objects.first()
    assert item is not None
    assert "1" in item.item_number
    
    motion = Motion.objects.first()
    assert motion is not None
    assert motion.mover.canonical_name == "Supervisor Gore"
    assert motion.seconder.canonical_name == "Supervisor Carrillo"

@pytest.mark.django_db
def test_lobbying_disclosure_ingestion():
    # Setup test document
    doc = Document.objects.create(
        original_filename="lobby_test.pdf",
        sha256_hash="dummy_hash_lobby"
    )
    
    # Page text containing lobby keywords
    page_text = """
    LOBBYING ACTIVITY REPORT
    Lobbyist Firm: Muelrath Public Affairs
    Client: Bellevue School District
    Agency: Sonoma County Board of Supervisors
    """
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text=page_text
    )
    
    # Run Ingestion
    generic_document_ingestion(doc)
    
    # Assert LobbyingActivity was created
    lobby = LobbyingActivity.objects.first()
    assert lobby is not None
    assert lobby.lobbyist_entity.canonical_name == "Muelrath Public Affairs"
    assert lobby.client_entity.canonical_name == "Bellevue School District"
