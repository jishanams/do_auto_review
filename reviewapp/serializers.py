# reviewapp/serializers.py

from rest_framework import serializers
from .models import Shop, Customer, Purchase

class BillDataSerializer(serializers.Serializer):
    """Serializer for incoming bill data"""
    customer_name = serializers.CharField(max_length=200)
    customer_phone = serializers.CharField(max_length=20)
    shop_name = serializers.CharField(max_length=200)
    bill_number = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = serializers.DateTimeField(required=False)

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone_number', 'shop', 'total_purchases']