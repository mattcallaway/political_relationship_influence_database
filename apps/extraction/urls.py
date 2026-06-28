from django.urls import path
from . import views

urlpatterns = [
    path('review/<uuid:document_id>/', views.review_side_by_side, name='review_side_by_side'),
]
