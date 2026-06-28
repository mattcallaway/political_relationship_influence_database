from django.shortcuts import render
from apps.documents.models import Document

def document_queue(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    return render(request, 'documents/document_queue.html', {'documents': documents})
