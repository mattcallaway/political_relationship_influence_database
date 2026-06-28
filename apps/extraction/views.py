from django.shortcuts import render

def review_side_by_side(request, document_id):
    return render(request, 'extraction/side_by_side.html', {'document_id': document_id})
