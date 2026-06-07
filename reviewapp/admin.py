# reviewapp/admin.py

from django.contrib import admin
from .models import Shop, Customer, Purchase, MessageLog

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_profile_id', 'whatsapp_number', 'created_at']
    search_fields = ['name']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'shop', 'total_purchases', 'created_at']
    search_fields = ['name', 'phone_number']
    list_filter = ['shop']

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'customer', 'amount', 'purchase_date']
    search_fields = ['bill_number']

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'shop']
    search_fields = ['customer__name', 'customer__phone_number']