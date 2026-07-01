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

def expenditure_list(request):
    from django.db.models import Q
    from django.http import HttpResponse
    from apps.transactions.models import Expenditure
    import csv
    
    payee = request.GET.get('payee', '').strip()
    committee = request.GET.get('committee', '').strip()
    code = request.GET.get('code', '').strip()
    cycle = request.GET.get('cycle', '').strip()
    min_amount = request.GET.get('min_amount', '').strip()
    max_amount = request.GET.get('max_amount', '').strip()
    export = request.GET.get('export', '')

    expenditures = Expenditure.objects.all().order_by('-transaction_date', '-amount')
    
    if payee:
        expenditures = expenditures.filter(Q(payee_raw_name__icontains=payee) | Q(payee_entity__canonical_name__icontains=payee))
    if committee:
        expenditures = expenditures.filter(filer_committee__canonical_name__icontains=committee)
    if code:
        expenditures = expenditures.filter(transaction_code=code)
    if cycle:
        try:
            expenditures = expenditures.filter(transaction_date__year=int(cycle))
        except ValueError:
            pass
    if min_amount:
        try:
            expenditures = expenditures.filter(amount__gte=float(min_amount))
        except ValueError:
            pass
    if max_amount:
        try:
            expenditures = expenditures.filter(amount__lte=float(max_amount))
        except ValueError:
            pass

    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenditures.csv"'
        writer = csv.writer(response)
        writer.writerow(['public_id', 'filer_committee', 'payee_raw_name', 'transaction_date', 'amount', 'transaction_code', 'description'])
        for e in expenditures:
            writer.writerow([
                e.public_id,
                e.filer_committee.canonical_name,
                e.payee_raw_name,
                e.transaction_date,
                e.amount,
                e.transaction_code,
                e.description
            ])
        return response

    return render(request, 'transactions/expenditure_list.html', {
        'expenditures': expenditures[:100],
        'payee': payee,
        'committee': committee,
        'code': code,
        'cycle': cycle,
        'min_amount': min_amount,
        'max_amount': max_amount
    })

def expenditure_detail(request, expenditure_id):
    from django.shortcuts import get_object_or_404
    from apps.transactions.models import Expenditure
    expenditure = get_object_or_404(Expenditure, id=expenditure_id)
    return render(request, 'transactions/expenditure_detail.html', {
        'expenditure': expenditure
    })

def expenditure_create(request):
    from django.shortcuts import redirect
    from apps.transactions.models import Expenditure, ReviewStatus
    from apps.entities.models import Entity
    from apps.sources.models import Source
    
    if request.method == 'POST':
        filer_committee_id = request.POST.get('filer_committee')
        payee_entity_id = request.POST.get('payee_entity')
        payee_raw_name = request.POST.get('payee_raw_name')
        amount = request.POST.get('amount')
        transaction_date = request.POST.get('transaction_date')
        description = request.POST.get('description', '')
        transaction_code = request.POST.get('transaction_code', '')
        source_id = request.POST.get('source')
        
        filer = Entity.objects.get(id=filer_committee_id)
        payee = Entity.objects.get(id=payee_entity_id) if payee_entity_id else None
        source = Source.objects.get(id=source_id) if source_id else None
        
        import random
        public_id = f"EXP{random.randint(100000, 999999)}"
        
        exp = Expenditure.objects.create(
            public_id=public_id,
            filer_committee=filer,
            payee_entity=payee,
            payee_raw_name=payee_raw_name or (payee.canonical_name if payee else ''),
            amount=amount,
            transaction_date=transaction_date or None,
            description=description,
            transaction_code=transaction_code,
            source=source,
            review_status=ReviewStatus.REVIEWED
        )
        return redirect('expenditure_detail', expenditure_id=exp.id)
        
    entities = Entity.objects.all().order_by('canonical_name')
    sources = Source.objects.all().order_by('title')
    return render(request, 'transactions/expenditure_form.html', {
        'entities': entities,
        'sources': sources
    })

def expenditure_edit(request, expenditure_id):
    from django.shortcuts import get_object_or_404, redirect
    from apps.transactions.models import Expenditure
    from apps.entities.models import Entity
    from apps.sources.models import Source
    
    exp = get_object_or_404(Expenditure, id=expenditure_id)
    if request.method == 'POST':
        filer_committee_id = request.POST.get('filer_committee')
        payee_entity_id = request.POST.get('payee_entity')
        payee_raw_name = request.POST.get('payee_raw_name')
        amount = request.POST.get('amount')
        transaction_date = request.POST.get('transaction_date')
        description = request.POST.get('description', '')
        transaction_code = request.POST.get('transaction_code', '')
        source_id = request.POST.get('source')
        
        exp.filer_committee = Entity.objects.get(id=filer_committee_id)
        exp.payee_entity = Entity.objects.get(id=payee_entity_id) if payee_entity_id else None
        exp.payee_raw_name = payee_raw_name or (exp.payee_entity.canonical_name if exp.payee_entity else '')
        exp.amount = amount
        exp.transaction_date = transaction_date or None
        exp.description = description
        exp.transaction_code = transaction_code
        exp.source = Source.objects.get(id=source_id) if source_id else None
        exp.save()
        
        return redirect('expenditure_detail', expenditure_id=exp.id)
        
    entities = Entity.objects.all().order_by('canonical_name')
    sources = Source.objects.all().order_by('title')
    return render(request, 'transactions/expenditure_form.html', {
        'expenditure': exp,
        'entities': entities,
        'sources': sources
    })

def expenditure_import_csv(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    from apps.transactions.models import Expenditure, ReviewStatus
    from apps.entities.models import Entity
    import io
    import csv
    import random
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        count = 0
        for row in reader:
            filer_name = row.get('filer_committee')
            payee_name = row.get('payee_raw_name')
            amount = row.get('amount')
            date_str = row.get('transaction_date')
            code = row.get('transaction_code', '')
            desc = row.get('description', '')
            
            filer = Entity.objects.filter(canonical_name__icontains=filer_name).first()
            if not filer:
                filer = Entity.objects.create(
                    public_id=f"ENT{random.randint(100000, 999999)}",
                    canonical_name=filer_name,
                    entity_type='COMMITTEE',
                    status='PROVISIONAL_AUTO_CREATED'
                )
                
            payee = Entity.objects.filter(canonical_name__icontains=payee_name).first()
            
            Expenditure.objects.create(
                public_id=f"EXP{random.randint(100000, 999999)}",
                filer_committee=filer,
                payee_entity=payee,
                payee_raw_name=payee_name,
                amount=amount,
                transaction_date=date_str or None,
                description=desc,
                transaction_code=code,
                review_status=ReviewStatus.AUTO_IMPORTED
            )
            count += 1
            
        messages.success(request, f"Successfully imported {count} expenditure records!")
        return redirect('expenditure_list')
        
    return render(request, 'transactions/expenditure_import.html', {})

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@require_POST
def trigger_reconciliation(request):
    from apps.audit.models import ImportBatch
    from apps.transactions.reconciliation import reconcile_amendment_batches
    
    old_batch_id = request.POST.get('old_batch_id')
    new_batch_id = request.POST.get('new_batch_id')
    
    old_batch = get_object_or_404(ImportBatch, id=old_batch_id)
    new_batch = get_object_or_404(ImportBatch, id=new_batch_id)
    
    reconcile_amendment_batches(old_batch, new_batch)
    
    messages.success(request, f"Successfully reconciled old batch '{old_batch.batch_name}' with new amendment batch '{new_batch.batch_name}'!")
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('imports_management')
