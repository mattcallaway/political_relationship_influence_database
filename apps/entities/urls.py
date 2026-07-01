from django.urls import path
from . import views

urlpatterns = [
    path('', views.entity_list, name='entity_list'),
    path('search/', views.unified_search, name='entity_search'),
    path('entity/<str:public_id>/', views.entity_detail, name='entity_detail'),
    path('entity/<str:public_id>/moderate/', views.entity_moderate, name='entity_moderate'),
]
