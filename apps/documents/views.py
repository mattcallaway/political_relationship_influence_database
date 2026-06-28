from django.shortcuts import render

def document_queue(request):
    return render(request, 'documents/document_queue.html', {})
