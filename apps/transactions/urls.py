from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('lobbying/', views.lobbying_list, name='lobbying_list'),
    path('contracts/', views.contract_list, name='contract_list'),
]
