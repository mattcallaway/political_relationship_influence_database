# tests/test_fppc460_extraction.py
import os
import json
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.documents.models import Document, DocumentPage, DocumentProcessingStatus
from apps.documents.services import process_document_pdf
from apps.extraction.services import parse_form_460
from apps.extraction.models import ExtractedField
from apps.extraction.evaluation import evaluate_extraction_on_page

@pytest.mark.django_db
def test_digital_netfile_extraction():
    # Path to test PDF
    pdf_path = r'data\uploads\documents\2026\06\Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf'
    assert os.path.exists(pdf_path), "Test PDF 25-01-2024.pdf must exist"
    
    # Create Document record
    with open(pdf_path, 'rb') as f:
        file_data = f.read()
        
    uploaded_file = SimpleUploadedFile(
        name=os.path.basename(pdf_path),
        content=file_data,
        content_type='application/pdf'
    )
    
    import hashlib
    sha256 = hashlib.sha256(file_data).hexdigest()
    
    # Clean previous if exists
    Document.objects.filter(sha256_hash=sha256).delete()
    
    doc = Document.objects.create(
        original_filename=uploaded_file.name,
        file_path=uploaded_file,
        byte_size=len(file_data),
        sha256_hash=sha256,
        media_type='application/pdf',
        processing_status=DocumentProcessingStatus.UPLOADED
    )
    
    # Process PDF (extract text)
    success = process_document_pdf(doc.id)
    assert success
    
    # Run the Form 460 parser
    job = parse_form_460(doc)
    assert job.status == 'COMPLETED'
    
    # Check that ExtractedFields are created
    fields = ExtractedField.objects.filter(extraction_job=job, page__page_number=4)
    block_fields = [f for f in fields if f.field_type.startswith("contribution_block_")]
    assert len(block_fields) == 3, f"Expected 3 visual contributor blocks on page 4, got {len(block_fields)}"
    
    # Parse payload of first block
    first_block_data = json.loads(block_fields[0].normalized_proposed_value)
    assert first_block_data["contributor_name"] == "Joshua Hochberg"
    assert first_block_data["amount"] == 2500.0
    assert first_block_data["date"] == "10/23/2023"
    assert first_block_data["contributor_code"] == "IND"
    assert first_block_data["occupation"] == "Owner"
    assert first_block_data["employer"] == "Sonoma Aviation"
    
    # Evaluate extraction accuracy
    records = []
    for bf in block_fields:
        records.append(json.loads(bf.normalized_proposed_value))
        
    metrics = evaluate_extraction_on_page(doc.original_filename, 4, records)
    assert metrics is not None
    assert metrics["precision"] == 100.0
    assert metrics["recall"] == 100.0
    assert metrics["name_accuracy"] == 100.0
    assert metrics["amount_accuracy"] == 100.0
    assert metrics["date_accuracy"] == 100.0

    # Verify Schedule E payments made extraction on Page 5
    fields_e = ExtractedField.objects.filter(extraction_job=job, page__page_number=5)
    block_fields_e = [f for f in fields_e if f.field_type.startswith("expenditure_block_")]
    assert len(block_fields_e) == 3, f"Expected 3 visual expenditure blocks on page 5, got {len(block_fields_e)}"

    first_exp_data = json.loads(block_fields_e[0].normalized_proposed_value)
    assert first_exp_data["payee_name"] == "ActBlue Technical Services"
    assert first_exp_data["amount"] == 0.90
    assert first_exp_data["payee_code"] == "OFC"

    # Verify database persistence
    from apps.transactions.models import Expenditure
    assert Expenditure.objects.filter(payee_raw_name="ActBlue Technical Services", amount=0.90).exists()

@pytest.mark.django_db
def test_scanned_pdf_mock_extraction():
    # We test the scanned PDF extraction using the mock OCR preprocessor path
    pdf_paths = [
        r'C:\Users\Mathew C\Downloads\Working Families & Environmentalists for a Better Sonoma County Opposing James Gore for Supervisor_fppc460_201_17-08-2015.pdf',
        r'C:\Users\Mathew C\Downloads\Working Families & Environmentalists for a Better Sonoma County Opposing James Gore for Supervisor_fppc460_201_28-12-2015.pdf'
    ]
    
    for p in pdf_paths:
        if not os.path.exists(p):
            continue
            
        with open(p, 'rb') as f:
            file_data = f.read()
            
        import hashlib
        sha256 = hashlib.sha256(file_data).hexdigest()
        Document.objects.filter(sha256_hash=sha256).delete()
        
        uploaded_file = SimpleUploadedFile(
            name=os.path.basename(p),
            content=file_data,
            content_type='application/pdf'
        )
        
        doc = Document.objects.create(
            original_filename=uploaded_file.name,
            file_path=uploaded_file,
            byte_size=len(file_data),
            sha256_hash=sha256,
            media_type='application/pdf',
            processing_status=DocumentProcessingStatus.UPLOADED
        )
        
        # Add mock pages
        for page_num in range(1, 7):
            DocumentPage.objects.create(
                document=doc,
                page_number=page_num,
                extracted_text="", # Scanned
                processing_status='COMPLETED'
            )
            
        # Run Form 460 parser
        job = parse_form_460(doc)
        assert job.status == 'COMPLETED'
        
        # Verify page 3 has extracted fields
        fields = ExtractedField.objects.filter(extraction_job=job, page__page_number=3)
        block_fields = [f for f in fields if f.field_type.startswith("contribution_block_")]
        assert len(block_fields) == 2, f"Expected 2 contributor blocks, got {len(block_fields)}"
        
        # Evaluate accuracy
        records = []
        for bf in block_fields:
            records.append(json.loads(bf.normalized_proposed_value))
            
        metrics = evaluate_extraction_on_page(doc.original_filename, 3, records)
        assert metrics is not None
        assert metrics["precision"] == 100.0
        assert metrics["recall"] == 100.0
        
        # For the second document, verify the intermediary (ActBlue) was correctly extracted
        if "28-12-2015" in p:
            second_block = records[1]
            assert second_block["contributor_name"] == "Carolyn Adkins"
            assert second_block["intermediary_name"] == "ActBlue"
            assert metrics["intermediary_accuracy"] == 100.0
