from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication - Login page first
    path(
        '',
        views.admin_login,
        name='admin_login'
    ),

    path(
        'logout/',
        views.admin_logout,
        name='admin_logout'
    ),

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),
    # API URLs
    path('api/receive-bill/', views.ReceiveBillAPI.as_view(), name='receive_bill'),
    path('api/dashboard/', views.DashboardView.as_view(), name='api_dashboard'),
    
    # Admin Dashboard
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    
    
    # Shop URLs
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/add/', views.shop_add, name='shop_add'),
    path('shops/edit/<int:shop_id>/', views.shop_edit, name='shop_edit'),
    path('shops/delete/<int:shop_id>/', views.shop_delete, name='shop_delete'),
    
    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/edit/<int:customer_id>/', views.customer_edit, name='customer_edit'),
    path('customers/delete/<int:customer_id>/', views.customer_delete, name='customer_delete'),
    
    # Purchase URLs
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    path('purchases/edit/<int:purchase_id>/', views.purchase_edit, name='purchase_edit'),
    path('purchases/delete/<int:purchase_id>/', views.purchase_delete, name='purchase_delete'),
    
    # Message URLs
    path('messages/', views.message_list, name='message_list'),
    path('messages/add/', views.message_add, name='message_add'),
    path('messages/edit/<int:message_id>/', views.message_edit, name='message_edit'),
    path('messages/delete/<int:message_id>/', views.message_delete, name='message_delete'),
    path('messages/resend/<int:message_id>/', views.message_resend, name='message_resend'),
    
    # Additional shops list
    path('shops-list/', views.shops_list, name='shops_list'),
]