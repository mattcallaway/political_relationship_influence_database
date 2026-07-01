import pytest
from django.test import Client
from apps.documents.models import Document, DocumentPage
from apps.sources.models import Source, SourceLocator
from apps.transactions.models import Contribution, Expenditure, ReviewStatus
from apps.assertions.models import Assertion, AssertionSource
from apps.entities.models import Entity

@pytest.mark.django_db
def test_document_workspace_ocr_correction():
    client = Client()
    
    # 1. Setup Document and DocumentPage
    doc = Document.objects.create(
        original_filename="test_file.pdf",
        sha256_hash="abcde12345" * 6,
        page_count=3
    )
    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="Original Raw Text",
        ocr_text=""
    )
    
    # 2. Verify initial GET request renders raw text
    response = client.get(f'/documents/{doc.id}/workspace/?page=1')
    assert response.status_code == 200
    html = response.content.decode()
    assert "Original Raw Text" in html
    
    # 3. Post OCR correction
    post_response = client.post(f'/documents/{doc.id}/page/1/correct-ocr/', {
        'ocr_text': 'Corrected Verified Text Layer'
    })
    assert post_response.status_code == 302
    
    # 4. Verify original text remains unchanged but OCR text is updated
    page.refresh_from_db()
    assert page.extracted_text == "Original Raw Text"
    assert page.ocr_text == "Corrected Verified Text Layer"
    assert page.review_status == 'REVIEWED'

@pytest.mark.django_db
def test_create_locator_and_binding():
    client = Client()
    
    doc = Document.objects.create(
        original_filename="evidence_doc.pdf",
        sha256_hash="12345abcde" * 6,
        page_count=2
    )
    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="Raw content here"
    )
    
    # Setup assertion to bind
    subject = Entity.objects.create(public_id='ENT_SUB_TEST_1', canonical_name='Alice Smith', entity_type='PERSON')
    obj = Entity.objects.create(public_id='ENT_OBJ_TEST_1', canonical_name='City of Santa Rosa', entity_type='ORGANIZATION')
    
    assertion = Assertion.objects.create(
        public_id='AST-COR-1',
        subject_entity=subject,
        predicate='principal_of',
        object_entity=obj,
        verification_status='UNVERIFIED'
    )
    
    # Create locator and bind to assertion
    post_response = client.post(f'/documents/{doc.id}/page/1/create-locator/', {
        'page_range': '1',
        'vx0': '0.1',
        'vy0': '0.2',
        'vx1': '0.8',
        'vy1': '0.9',
        'section': 'Schedule A',
        'table_identifier': 'Row 5',
        'locator_description': 'Snippet showing Alice principal of Santa Rosa',
        'bind_target_type': 'assertion',
        'bind_target_id': str(assertion.id)
    })
    
    assert post_response.status_code == 302
    
    # Check locator creation
    locator = SourceLocator.objects.get(document=doc, page=page)
    assert locator.page_range == '1'
    assert locator.section == 'Schedule A'
    assert locator.bounding_box_json == [0.1, 0.2, 0.8, 0.9]
    
    # Check binding
    assert AssertionSource.objects.filter(assertion=assertion, source_locator=locator).exists()
