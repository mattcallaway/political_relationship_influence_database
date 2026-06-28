from django.shortcuts import render

def assertion_list(request):
    return render(request, 'assertions/assertion_list.html', {})
