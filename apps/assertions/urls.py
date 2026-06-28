from django.urls import path
from . import views

urlpatterns = [
    path('', views.assertion_list, name='assertion_list'),
]
