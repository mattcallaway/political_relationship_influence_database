from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('lobbying/', views.lobbying_list, name='lobbying_list'),
    path('contracts/', views.contract_list, name='contract_list'),
    path('expenditures/', views.expenditure_list, name='expenditure_list'),
    path('expenditures/create/', views.expenditure_create, name='expenditure_create'),
    path('expenditures/import/', views.expenditure_import_csv, name='expenditure_import_csv'),
    path('expenditures/<uuid:expenditure_id>/', views.expenditure_detail, name='expenditure_detail'),
    path('expenditures/<uuid:expenditure_id>/edit/', views.expenditure_edit, name='expenditure_edit'),
]
