from django.shortcuts import render

def transaction_list(request):
    return render(request, 'transactions/transaction_list.html', {})
