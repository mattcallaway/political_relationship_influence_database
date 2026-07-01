from django.urls import path
from . import views

urlpatterns = [
    path('', views.research_dashboard, name='research_dashboard'),
    path('tasks/', views.research_tasks, name='research_tasks'),
    path('data-quality/', views.data_quality, name='data_quality'),
    path('imports/', views.imports_management, name='imports_management'),
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/<uuid:collection_id>/', views.collection_detail, name='collection_detail'),
    path('network/', views.network_explorer, name='network_explorer'),
    path('compare/', views.compare_entities, name='compare_entities'),
]
