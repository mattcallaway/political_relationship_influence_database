from django.shortcuts import render, get_object_or_404
from apps.documents.models import Document
from apps.extraction.models import ExtractedField

def review_side_by_side(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    fields = ExtractedField.objects.filter(extraction_job__document=document)
    return render(request, 'extraction/side_by_side.html', {
        'document': document,
        'fields': fields
    })
