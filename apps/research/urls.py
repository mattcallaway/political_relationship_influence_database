from django.urls import path
from . import views

urlpatterns = [
    path('', views.research_dashboard, name='research_dashboard'),
]
