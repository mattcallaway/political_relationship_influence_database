from django.shortcuts import render

def source_list(request):
    return render(request, 'sources/source_list.html', {})
