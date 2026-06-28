import hashlib
import fitz  # PyMuPDF
from django.core.files.base import ContentFile
from apps.documents.models import Document, DocumentPage, DocumentProcessingStatus

def calculate_sha256(file_obj):
    sha256 = hashlib.sha256()
    for chunk in file_obj.chunks():
        sha256.update(chunk)
    file_obj.seek(0)
    return sha256.hexdigest()

def process_document_pdf(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        doc.processing_status = DocumentProcessingStatus.EXTRACTING
        doc.save()

        pdf_path = doc.file_path.path
        fitz_doc = fitz.open(pdf_path)
        doc.page_count = len(fitz_doc)
        has_text = False

        for page_num in range(len(fitz_doc)):
            page = fitz_doc[page_num]
            text = page.get_text()
            if text and len(text.strip()) > 10:
                has_text = True
            
            DocumentPage.objects.update_or_create(
                document=doc,
                page_number=page_num + 1,
                defaults={'extracted_text': text, 'processing_status': 'COMPLETED'}
            )

        doc.has_native_text = has_text
        doc.processing_status = DocumentProcessingStatus.EXTRACTION_COMPLETE
        doc.save()
        return True
    except Exception as e:
        if 'doc' in locals():
            doc.processing_status = DocumentProcessingStatus.FAILED
            doc.save()
        raise e
