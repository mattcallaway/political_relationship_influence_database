from django.shortcuts import render
from apps.transactions.models import Contribution, LobbyingActivity, Contract

def transaction_list(request):
    from django.db.models import Q
    
    donor = request.GET.get('donor', '').strip()
    recipient = request.GET.get('recipient', '').strip()
    cycle = request.GET.get('cycle', '').strip()
    min_amount = request.GET.get('min_amount', '').strip()
    max_amount = request.GET.get('max_amount', '').strip()
    
    contributions = Contribution.objects.all().order_by('-transaction_date', '-amount')
    
    if donor:
        contributions = contributions.filter(Q(donor_raw_name__icontains=donor) | Q(donor_entity__canonical_name__icontains=donor))
    if recipient:
        contributions = contributions.filter(filer_committee__canonical_name__icontains=recipient)
    if cycle:
        try:
            contributions = contributions.filter(transaction_date__year=int(cycle))
        except ValueError:
            pass
    if min_amount:
        try:
            contributions = contributions.filter(amount__gte=float(min_amount))
        except ValueError:
            pass
    if max_amount:
        try:
            contributions = contributions.filter(amount__lte=float(max_amount))
        except ValueError:
            pass
            
    return render(request, 'transactions/transaction_list.html', {
        'contributions': contributions[:100],
        'donor': donor,
        'recipient': recipient,
        'cycle': cycle,
        'min_amount': min_amount,
        'max_amount': max_amount
    })

def lobbying_list(request):
    lobbying_activities = LobbyingActivity.objects.all().order_by('-reporting_period')
    return render(request, 'transactions/lobbying_list.html', {
        'lobbying_activities': lobbying_activities[:100]
    })

def contract_list(request):
    contracts = Contract.objects.all().order_by('-execution_date')
    return render(request, 'transactions/contract_list.html', {
        'contracts': contracts[:100]
    })
