from django.shortcuts import render
from apps.sources.models import Source

def source_list(request):
    sources = Source.objects.all().order_by('-publication_date')
    return render(request, 'sources/source_list.html', {
        'sources': sources
    })
