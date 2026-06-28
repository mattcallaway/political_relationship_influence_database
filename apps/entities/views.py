from django.shortcuts import render
from django.http import HttpResponse

def entity_list(request):
    return render(request, 'entities/entity_list.html', {})

def entity_detail(request, public_id):
    return render(request, 'entities/entity_detail.html', {'public_id': public_id})
