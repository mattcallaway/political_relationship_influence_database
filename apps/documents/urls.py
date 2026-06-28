from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_queue, name='document_queue'),
]
