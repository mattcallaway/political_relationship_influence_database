from django.urls import path
from . import views

urlpatterns = [
    path('', views.source_list, name='source_list'),
]
