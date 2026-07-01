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
