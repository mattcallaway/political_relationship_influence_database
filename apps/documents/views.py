import os
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from apps.documents.models import Document, DocumentProcessingStatus
from apps.documents.services import calculate_sha256, process_document_pdf
from apps.extraction.services import parse_form_460

def document_queue(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    return render(request, 'documents/document_queue.html', {'documents': documents})

def upload_document(request):
    if request.method == 'POST' and request.FILES.getlist('document_file'):
        uploaded_files = request.FILES.getlist('document_file')
        for uploaded_file in uploaded_files:
            # Calculate SHA-256
            sha256_hash = calculate_sha256(uploaded_file)
            
            # Check duplicate
            existing_doc = Document.objects.filter(sha256_hash=sha256_hash).first()
            if existing_doc:
                continue
                
            doc = Document.objects.create(
                original_filename=uploaded_file.name,
                file_path=uploaded_file,
                byte_size=uploaded_file.size,
                sha256_hash=sha256_hash,
                media_type=uploaded_file.content_type or 'application/pdf',
                processing_status=DocumentProcessingStatus.UPLOADED
            )
            
            # Run synchronous text extraction & Form 460 parsing
            try:
                process_document_pdf(doc.id)
                parse_form_460(doc)
            except Exception:
                pass
                
        return redirect('document_queue')
        
    return redirect('document_queue')

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.documents.models import Document, DocumentPage
from apps.sources.models import Source, SourceLocator
from apps.transactions.models import Contribution, Expenditure
from apps.assertions.models import Assertion, AssertionSource
from apps.entities.models import Entity

def document_workspace(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    page_number = int(request.GET.get('page', 1))
    
    # Ensure page number is within bounds
    if page_number < 1:
        page_number = 1
    elif doc.page_count > 0 and page_number > doc.page_count:
        page_number = doc.page_count
        
    # Get or create the DocumentPage
    current_page, created = DocumentPage.objects.get_or_create(
        document=doc,
        page_number=page_number,
        defaults={'extracted_text': '', 'processing_status': 'COMPLETED'}
    )
    
    # Compile derived records associated with this document
    contributions = doc.contributions.all()
    expenditures = Expenditure.objects.filter(document_page__document=doc)
    
    # Connect assertions through AssertionSource -> SourceLocator -> Document
    assertions = Assertion.objects.filter(
        evidence_sources__source_locator__document=doc
    ).distinct()
    
    # Active source locators for this document
    locators = SourceLocator.objects.filter(document=doc)
    
    # Lookups for connection drop-down lists
    entities = Entity.objects.exclude(status='MERGED').order_by('canonical_name')
    assertions_all = Assertion.objects.all().order_by('public_id')
    
    return render(request, 'documents/document_workspace.html', {
        'document': doc,
        'current_page': current_page,
        'page_number': page_number,
        'prev_page': page_number - 1 if page_number > 1 else None,
        'next_page': page_number + 1 if page_number < doc.page_count else None,
        'contributions': contributions,
        'expenditures': expenditures,
        'assertions': assertions,
        'locators': locators,
        'entities': entities,
        'assertions_all': assertions_all,
    })

@require_POST
def correct_ocr(request, document_id, page_number):
    doc = get_object_or_404(Document, id=document_id)
    page = get_object_or_404(DocumentPage, document=doc, page_number=page_number)
    
    ocr_text = request.POST.get('ocr_text', '')
    page.ocr_text = ocr_text
    page.review_status = 'REVIEWED'
    page.save()
    
    messages.success(request, f"OCR text corrected and saved for page {page_number}")
    return redirect(f"/documents/{document_id}/workspace/?page={page_number}")

@require_POST
def create_locator(request, document_id, page_number):
    doc = get_object_or_404(Document, id=document_id)
    page = get_object_or_404(DocumentPage, document=doc, page_number=page_number)
    
    # 1. Resolve parent Source object (create one if document doesn't have one)
    source = doc.source
    if not source:
        import random
        source = Source.objects.create(
            public_id=f"SRC{random.randint(100000, 999999)}",
            title=f"Source for {doc.original_filename}",
            source_type='OTHER'
        )
        doc.source = source
        doc.save()
        
    page_range = request.POST.get('page_range', str(page_number))
    vx0 = request.POST.get('vx0')
    vy0 = request.POST.get('vy0')
    vx1 = request.POST.get('vx1')
    vy1 = request.POST.get('vy1')
    
    bbox = None
    if vx0 and vy0 and vx1 and vy1:
        try:
            bbox = [float(vx0), float(vy0), float(vx1), float(vy1)]
        except ValueError:
            pass
            
    locator = SourceLocator.objects.create(
        source=source,
        document=doc,
        page=page,
        page_range=page_range,
        bounding_box_json=bbox,
        section=request.POST.get('section', ''),
        table_identifier=request.POST.get('table_identifier', ''),
        agenda_item=request.POST.get('agenda_item', ''),
        filing_schedule=request.POST.get('filing_schedule', ''),
        locator_description=request.POST.get('locator_description', '')
    )
    
    # 2. Bind locator to the target record if selected
    bind_target_type = request.POST.get('bind_target_type')
    bind_target_id = request.POST.get('bind_target_id')
    
    if bind_target_id:
        if bind_target_type == 'assertion':
            assertion = get_object_or_404(Assertion, id=bind_target_id)
            # Create AssertionSource linking the assertion to the locator
            AssertionSource.objects.create(
                assertion=assertion,
                source=source,
                document_page=page,
                source_locator=locator,
                support_type='PRIMARY',
                evidence_note=locator.locator_description
            )
            messages.success(request, f"Bound locator to assertion '{assertion.public_id}'")
        elif bind_target_type == 'contribution':
            contrib = get_object_or_404(Contribution, id=bind_target_id)
            contrib.document_page = page
            contrib.source_locator = str(locator.id)
            contrib.save()
            messages.success(request, f"Bound locator to contribution '{contrib.public_id}'")
        elif bind_target_type == 'expenditure':
            exp = get_object_or_404(Expenditure, id=bind_target_id)
            exp.document_page = page
            exp.source_locator = str(locator.id)
            exp.save()
            messages.success(request, f"Bound locator to expenditure '{exp.public_id}'")
            
    messages.success(request, f"SourceLocator created on page {page_number}")
    return redirect(f"/documents/{document_id}/workspace/?page={page_number}")
