from django.shortcuts import render
from apps.government.models import GovernmentBody, PublicOffice, Meeting, Motion, Vote

def government_dashboard(request):
    bodies = GovernmentBody.objects.all()
    offices = PublicOffice.objects.all()
    meetings = Meeting.objects.all().order_by('-date')
    motions = Motion.objects.all()
    votes = Vote.objects.all().order_by('-meeting_date')
    
    return render(request, 'government/government_dashboard.html', {
        'bodies': bodies,
        'offices': offices,
        'meetings': meetings,
        'motions': motions,
        'votes': votes
    })
