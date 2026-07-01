from django.urls import path
from . import views

urlpatterns = [
    path('', views.research_dashboard, name='research_dashboard'),
    path('tasks/', views.research_tasks, name='research_tasks'),
    path('data-quality/', views.data_quality, name='data_quality'),
    path('imports/', views.imports_management, name='imports_management'),
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/<uuid:collection_id>/', views.collection_detail, name='collection_detail'),
    path('collections/<uuid:collection_id>/add/', views.add_to_collection, name='add_to_collection'),
    path('collections/<uuid:collection_id>/task/create/', views.create_collection_task, name='create_collection_task'),
    path('collections/<uuid:collection_id>/question/create/', views.create_collection_question, name='create_collection_question'),
    path('collections/add-item/', views.add_item_to_collection, name='add_item_to_collection'),
    path('network/', views.network_explorer, name='network_explorer'),
    path('compare/', views.compare_entities, name='compare_entities'),
    path('inventory/download/', views.download_inventory, name='download_inventory'),
    path('methodology/', views.methodology_page, name='methodology_page'),
]
