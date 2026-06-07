# reviewapp/views.py - Complete version with login authentication

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
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


# ==================== LOGIN & AUTHENTICATION VIEWS ====================

def custom_login(request):
    """Custom login page for admin"""
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('login')
    
    return render(request, 'admin/login.html')


def custom_logout(request):
    """Logout user"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


# ==================== API VIEWS ====================

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
            messages_log = MessageLog.objects.filter(shop=shop)
            stats[shop.name] = {
                'total_messages': messages_log.count(),
                'sent_messages': messages_log.filter(status='sent').count(),
                'failed_messages': messages_log.filter(status='failed').count(),
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


# reviewapp/views.py - Complete corrected version

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import models  # Add this for Sum aggregation
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


# ==================== LOGIN & AUTHENTICATION VIEWS ====================

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def admin_login(request):

    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('admin_dashboard')

        else:

            messages.error(
                request,
                "Invalid Username or Password"
            )

    return render(
        request,
        'admin_login.html'
    )


def admin_logout(request):

    logout(request)

    return redirect('admin_login')


# ==================== API VIEWS ====================

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
            messages_log = MessageLog.objects.filter(shop=shop)
            stats[shop.name] = {
                'total_messages': messages_log.count(),
                'sent_messages': messages_log.filter(status='sent').count(),
                'failed_messages': messages_log.filter(status='failed').count(),
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


# ==================== ADMIN DASHBOARD ====================

@login_required(login_url='login')
def admin_dashboard(request):
    context = {
        'total_shops': Shop.objects.count(),
        'total_customers': Customer.objects.count(),
        'total_purchases': Purchase.objects.count(),
        'total_messages': MessageLog.objects.count(),
        'sent_messages': MessageLog.objects.filter(status='sent').count(),
        'failed_messages': MessageLog.objects.filter(status='failed').count(),
        'duplicate_messages': MessageLog.objects.filter(status='duplicate').count(),
        'recent_messages': MessageLog.objects.select_related('customer', 'shop').order_by('-created_at')[:10],
    }
    return render(request, 'admin/dashboard.html', context)


# ==================== SHOP VIEWS ====================

@login_required(login_url='login')
def shop_list(request):
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'admin/shops.html', {'shops': shops})


@login_required(login_url='login')
def shop_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        whatsapp_number = request.POST.get('whatsapp_number')
        google_review_url = request.POST.get('google_review_url', '')
        
        shop = Shop.objects.create(
            name=name,
            whatsapp_number=whatsapp_number,
            google_review_url=google_review_url
        )
        messages.success(request, f'Shop "{name}" added successfully!')
        return redirect('shop_list')
    
    return render(request, 'admin/shop_form.html', {'action': 'Add'})


@login_required(login_url='login')
def shop_edit(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.method == 'POST':
        shop.name = request.POST.get('name')
        shop.whatsapp_number = request.POST.get('whatsapp_number')
        shop.google_review_url = request.POST.get('google_review_url', '')
        shop.save()
        messages.success(request, f'Shop "{shop.name}" updated successfully!')
        return redirect('shop_list')
    
    return render(request, 'admin/shop_form.html', {'shop': shop, 'action': 'Edit'})


@login_required(login_url='login')
def shop_delete(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop_name = shop.name
    shop.delete()
    messages.warning(request, f'Shop "{shop_name}" has been deleted!')
    return redirect('shop_list')


# ==================== CUSTOMER VIEWS ====================

@login_required(login_url='login')
def customer_list(request):
    customers = Customer.objects.select_related('shop').all().order_by('-created_at')
    return render(request, 'admin/customers.html', {'customers': customers})


@login_required(login_url='login')
def customer_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        shop_id = request.POST.get('shop_id')
        
        shop = None
        if shop_id:
            shop = get_object_or_404(Shop, id=shop_id)
        
        customer = Customer.objects.create(
            name=name,
            phone_number=phone_number,
            shop=shop
        )
        messages.success(request, f'Customer "{name}" added successfully!')
        return redirect('customer_list')
    
    shops = Shop.objects.all()
    return render(request, 'admin/customer_form.html', {'shops': shops, 'action': 'Add'})


@login_required(login_url='login')
def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.phone_number = request.POST.get('phone_number')
        shop_id = request.POST.get('shop_id')
        customer.shop = get_object_or_404(Shop, id=shop_id) if shop_id else None
        customer.save()
        messages.success(request, f'Customer "{customer.name}" updated successfully!')
        return redirect('customer_list')
    
    shops = Shop.objects.all()
    return render(request, 'admin/customer_form.html', {'customer': customer, 'shops': shops, 'action': 'Edit'})


@login_required(login_url='login')
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer_name = customer.name
    customer.delete()
    messages.warning(request, f'Customer "{customer_name}" has been deleted!')
    return redirect('customer_list')


# ==================== PURCHASE VIEWS ====================

@login_required(login_url='login')
def purchase_list(request):
    purchases = Purchase.objects.select_related('customer', 'shop').order_by('-purchase_date')
    return render(request, 'admin/purchases.html', {'purchases': purchases})


@login_required(login_url='login')
def purchase_add(request):
    if request.method == 'POST':
        bill_number = request.POST.get('bill_number')
        customer_id = request.POST.get('customer_id')
        shop_id = request.POST.get('shop_id')
        amount = request.POST.get('amount')
        
        customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
        shop = get_object_or_404(Shop, id=shop_id) if shop_id else None
        
        purchase = Purchase.objects.create(
            bill_number=bill_number,
            customer=customer,
            shop=shop,
            amount=amount
        )
        messages.success(request, f'Purchase #{bill_number} added successfully!')
        return redirect('purchase_list')
    
    customers = Customer.objects.all()
    shops = Shop.objects.all()
    return render(request, 'admin/purchase_form.html', {'customers': customers, 'shops': shops, 'action': 'Add'})


@login_required(login_url='login')
def purchase_edit(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    if request.method == 'POST':
        purchase.bill_number = request.POST.get('bill_number')
        customer_id = request.POST.get('customer_id')
        shop_id = request.POST.get('shop_id')
        purchase.customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
        purchase.shop = get_object_or_404(Shop, id=shop_id) if shop_id else None
        purchase.amount = request.POST.get('amount')
        purchase.save()
        messages.success(request, f'Purchase #{purchase.bill_number} updated successfully!')
        return redirect('purchase_list')
    
    customers = Customer.objects.all()
    shops = Shop.objects.all()
    return render(request, 'admin/purchase_form.html', {'purchase': purchase, 'customers': customers, 'shops': shops, 'action': 'Edit'})


@login_required(login_url='login')
def purchase_delete(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    bill_number = purchase.bill_number
    purchase.delete()
    messages.warning(request, f'Purchase #{bill_number} has been deleted!')
    return redirect('purchase_list')


# ==================== MESSAGE VIEWS ====================

@login_required(login_url='login')
def message_list(request):
    messages_log = MessageLog.objects.select_related('customer', 'shop').order_by('-created_at')
    return render(request, 'admin/messages.html', {'messages': messages_log})


@login_required(login_url='login')
def message_add(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        shop_id = request.POST.get('shop_id')
        review_link = request.POST.get('review_link')
        status = request.POST.get('status', 'pending')
        
        customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
        shop = get_object_or_404(Shop, id=shop_id) if shop_id else None
        
        message = MessageLog.objects.create(
            customer=customer,
            shop=shop,
            review_link=review_link,
            status=status
        )
        messages.success(request, f'Message sent to {customer.name if customer else "customer"}!')
        return redirect('message_list')
    
    customers = Customer.objects.all()
    shops = Shop.objects.all()
    return render(request, 'admin/message_form.html', {'customers': customers, 'shops': shops, 'action': 'Send'})


@login_required(login_url='login')
def message_edit(request, message_id):
    message = get_object_or_404(MessageLog, id=message_id)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        shop_id = request.POST.get('shop_id')
        message.customer = get_object_or_404(Customer, id=customer_id) if customer_id else None
        message.shop = get_object_or_404(Shop, id=shop_id) if shop_id else None
        message.review_link = request.POST.get('review_link')
        message.status = request.POST.get('status')
        message.save()
        messages.success(request, f'Message updated successfully!')
        return redirect('message_list')
    
    customers = Customer.objects.all()
    shops = Shop.objects.all()
    return render(request, 'admin/message_form.html', {'message': message, 'customers': customers, 'shops': shops, 'action': 'Edit'})


@login_required(login_url='login')
def message_delete(request, message_id):
    message = get_object_or_404(MessageLog, id=message_id)
    message.delete()
    messages.warning(request, 'Message deleted successfully!')
    return redirect('message_list')


@login_required(login_url='login')
def message_resend(request, message_id):
    message = get_object_or_404(MessageLog, id=message_id)
    # Resend logic here (WhatsApp API integration)
    message.status = 'sent'
    message.save()
    messages.success(request, f'Message resent to {message.customer.name if message.customer else "customer"}!')
    return redirect('message_list')


@login_required(login_url='login')
def shops_list(request):
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'shops.html', {'shops': shops})