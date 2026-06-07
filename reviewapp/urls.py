

from django.urls import path
from . import views

urlpatterns = [
    path('api/receive-bill/', views.ReceiveBillAPI.as_view(), name='receive_bill'),
    path('api/dashboard/', views.DashboardView.as_view(), name='dashboard'),
]