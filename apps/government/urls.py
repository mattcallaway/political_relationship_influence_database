from django.urls import path
from . import views

urlpatterns = [
    path('', views.government_dashboard, name='government_dashboard'),
]
