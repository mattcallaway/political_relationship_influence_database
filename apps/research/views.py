from django.shortcuts import render

def research_dashboard(request):
    return render(request, 'research/dashboard.html', {})
