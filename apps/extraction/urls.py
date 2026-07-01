from django.urls import path
from . import views

urlpatterns = [
    path('queue/', views.review_queue, name='review_queue'),
    path('review/<uuid:document_id>/', views.review_side_by_side, name='review_side_by_side'),
    path('confirm/<uuid:contribution_id>/', views.confirm_match, name='confirm_match'),
    path('rematch/<uuid:contribution_id>/', views.rematch_contribution, name='rematch_contribution'),
    path('merge/<uuid:source_entity_id>/', views.merge_entities, name='merge_entities'),
    path('merge/reverse/<uuid:merge_id>/', views.reverse_entity_merge, name='reverse_entity_merge'),
    path('reject/<uuid:contribution_id>/', views.reject_contribution, name='reject_contribution'),
    path('correct/<uuid:contribution_id>/', views.correct_contribution_fields, name='correct_contribution_fields'),
]
