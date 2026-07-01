from django.urls import path
from . import views

urlpatterns = [
    path('', views.assertion_list, name='assertion_list'),
    path('create/', views.create_assertion, name='assertion_create'),
    path('edit/<uuid:assertion_id>/', views.edit_assertion, name='assertion_edit'),
]
