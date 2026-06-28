from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_queue, name='document_queue'),
    path('upload/', views.upload_document, name='upload_document'),
]
