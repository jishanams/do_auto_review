# reviewapp/views.py - Modified version

from django.utils import timezone
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from .models import Shop, Customer, Purchase, MessageLog
from .serializers import BillDataSerializer
import json
import logging

# Try to import utils, handle if not exists
try:
    from .utils import send_whatsapp_message
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    logging.warning("utils.py not found. WhatsApp functionality disabled.")

@method_decorator(csrf_exempt, name='dispatch')
class ReceiveBillAPI(APIView):
    """
    API endpoint to receive bill data from billing system
    POST /api/receive-bill/
    """
    
    def post(self, request):
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except:
            data = request.data
        
        serializer = BillDataSerializer(data=data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get or create shop
        shop, _ = Shop.objects.get_or_create(
            name=validated_data['shop_name'],
            defaults={
                'business_profile_id': 'your-default-id',
                'whatsapp_number': ''
            }
        )
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            phone_number=validated_data['customer_phone'],
            shop=shop,
            defaults={
                'name': validated_data['customer_name']
            }
        )
        
        # Update customer name if different
        if not created and customer.name != validated_data['customer_name']:
            customer.name = validated_data['customer_name']
            customer.save()
        
        # Create purchase record
        purchase = Purchase.objects.create(
            customer=customer,
            shop=shop,
            amount=validated_data['amount'],
            bill_number=validated_data['bill_number'],
            purchase_date=validated_data.get('purchase_date', timezone.now())
        )
        
        # Update customer stats
        customer.total_purchases += 1
        customer.total_amount += validated_data['amount']
        customer.save()
        
        # Check if message already sent today
        today = timezone.now().date()
        message_sent_today = MessageLog.objects.filter(
            customer=customer,
            sent_at__date=today,
            status='sent'
        ).exists()
        
        if message_sent_today:
            MessageLog.objects.create(
                customer=customer,
                shop=shop,
                purchase=purchase,
                message_content="Duplicate - Already sent today",
                review_link=shop.get_google_review_url(),
                status='duplicate'
            )
            return Response({
                'status': 'duplicate',
                'message': 'Message already sent to this customer today'
            }, status=status.HTTP_200_OK)
        
        # Prepare message content
        message_content = f"""Dear {customer.name},

Thank you for shopping with us at {shop.name}! We truly appreciate your trust and support.

It would mean the world to us if you could take 30 seconds to share your experience — your feedback helps other customers and helps us grow.

Leave a Google Review:
{shop.get_google_review_url()}

Thank you once again!
Team {shop.name}"""
        
        # Send WhatsApp message (if utils available)
        if UTILS_AVAILABLE:
            whatsapp_result = send_whatsapp_message(customer.phone_number, message_content)
        else:
            # Mock response for development
            whatsapp_result = {
                'success': True,
                'message_id': 'mock_message_id',
                'error': None
            }
        
        # Log the message
        message_log = MessageLog.objects.create(
            customer=customer,
            shop=shop,
            purchase=purchase,
            message_content=message_content,
            review_link=shop.get_google_review_url(),
            status='sent' if whatsapp_result.get('success') else 'failed',
            whatsapp_message_id=whatsapp_result.get('message_id', ''),
            error_message=whatsapp_result.get('error', ''),
            sent_at=timezone.now() if whatsapp_result.get('success') else None
        )
        
        return Response({
            'status': 'success' if whatsapp_result.get('success') else 'failed',
            'customer_id': customer.id,
            'purchase_id': purchase.id,
            'message_id': message_log.id,
            'whatsapp_response': whatsapp_result
        }, status=status.HTTP_200_OK if whatsapp_result.get('success') else status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardView(APIView):
    """Dashboard for shop owners"""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        shops = Shop.objects.all()
        
        stats = {}
        for shop in shops:
            messages = MessageLog.objects.filter(shop=shop)
            stats[shop.name] = {
                'total_messages': messages.count(),
                'sent_messages': messages.filter(status='sent').count(),
                'failed_messages': messages.filter(status='failed').count(),
                'customers': Customer.objects.filter(shop=shop).count(),
                'total_sales': Purchase.objects.filter(shop=shop).aggregate(total=models.Sum('amount'))['total'] or 0
            }
        
        recent_messages = MessageLog.objects.all().order_by('-created_at')[:50]
        
        return Response({
            'stats': stats,
            'recent_messages': [
                {
                    'customer': msg.customer.name,
                    'shop': msg.shop.name,
                    'status': msg.status,
                    'sent_at': msg.sent_at,
                } for msg in recent_messages
            ]
        })


@login_required
def dashboard_html(request):
    """Render HTML dashboard for shop owners"""
    return render(request, 'dashboard.html')