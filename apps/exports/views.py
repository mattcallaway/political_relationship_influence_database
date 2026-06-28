from django.http import HttpResponse

def export_index(request):
    return HttpResponse("Exports API / Downloads")
