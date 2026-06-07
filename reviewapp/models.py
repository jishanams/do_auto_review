# reviewapp/models.py

from django.db import models
from django.utils import timezone

class Shop(models.Model):
    """Store/shop information"""
    name = models.CharField(max_length=200)
    business_profile_id = models.CharField(max_length=100, help_text="Google Business Profile ID")
    whatsapp_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_google_review_url(self):
        """Generate Google review link for this shop"""
        return f"https://g.page/r/{self.business_profile_id}/review"

class Customer(models.Model):
    """Customer information"""
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, db_index=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='customers')
    total_purchases = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['phone_number', 'shop']  # Same customer, same shop unique
    
    def __str__(self):
        return f"{self.name} - {self.phone_number}"

class Purchase(models.Model):
    """Individual purchase transaction"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='purchases')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bill_number = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Bill: {self.bill_number} - ₹{self.amount}"

class MessageLog(models.Model):
    """Track all WhatsApp messages sent"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('duplicate', 'Duplicate - Already Sent'),
        ('pending', 'Pending'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='messages')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, null=True, blank=True)
    message_content = models.TextField()
    review_link = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    whatsapp_message_id = models.CharField(max_length=255, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message to {self.customer.name} - {self.status}"