from django.urls import path
from . import views

urlpatterns = [
    path('<str:public_id>/', views.campaign_detail, name='campaign_detail'),
]
