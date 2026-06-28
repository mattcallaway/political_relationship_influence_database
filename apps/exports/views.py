from django.shortcuts import render
from django.http import HttpResponse
from apps.exports.services import export_entities_csv, export_network_graphml

def export_index(request):
    fmt = request.GET.get('format', '')
    if fmt == 'csv':
        response = HttpResponse(export_entities_csv(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sonoma_entities.csv"'
        return response
    elif fmt == 'graphml':
        response = HttpResponse(export_network_graphml(), content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="sonoma_network.graphml"'
        return response
    return render(request, 'exports/export_index.html', {})
