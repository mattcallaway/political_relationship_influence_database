from django.shortcuts import render
from apps.entities.models import Project

def project_list(request):
    projects = Project.objects.all().order_by('entity__canonical_name')
    return render(request, 'projects/project_list.html', {
        'projects': projects
    })
