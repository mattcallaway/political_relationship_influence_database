from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_queue, name='document_queue'),
    path('upload/', views.upload_document, name='upload_document'),
    path('<uuid:document_id>/workspace/', views.document_workspace, name='document_workspace'),
    path('<uuid:document_id>/page/<int:page_number>/correct-ocr/', views.correct_ocr, name='correct_ocr'),
    path('<uuid:document_id>/page/<int:page_number>/create-locator/', views.create_locator, name='create_locator'),
]
