# reviewapp/utils.py

import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number, message):
    """
    Send WhatsApp message using Meta Cloud API
    """
    # Format phone number (remove + if present, ensure country code)
    phone_number = phone_number.replace('+', '').strip()
    
    # Get WhatsApp configuration from settings
    whatsapp_token = getattr(settings, 'WHATSAPP_TOKEN', None)
    whatsapp_phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    
    # If WhatsApp is not configured, return mock response for development
    if not whatsapp_token or not whatsapp_phone_number_id:
        logger.warning("WhatsApp not configured. Running in demo mode.")
        return {
            'success': True,
            'message_id': 'demo_message_id_123',
            'response': {'demo': True, 'message': 'WhatsApp not configured - Demo mode'},
            'error': None
        }
    
    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json",
    }
    
    # For text message
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": message
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message_id': response_data.get('messages', [{}])[0].get('id', ''),
                'response': response_data,
                'error': None
            }
        else:
            return {
                'success': False,
                'message_id': None,
                'response': response_data,
                'error': response_data.get('error', {}).get('message', 'Unknown error')
            }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message_id': None,
            'response': None,
            'error': 'Request timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'message_id': None,
            'response': None,
            'error': str(e)
        }


def send_template_message(phone_number, template_name, language, components):
    """
    Send a pre-approved template message
    """
    phone_number = phone_number.replace('+', '').strip()
    
    whatsapp_token = getattr(settings, 'WHATSAPP_TOKEN', None)
    whatsapp_phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    
    if not whatsapp_token or not whatsapp_phone_number_id:
        return {
            'success': True,
            'message_id': 'demo_template_id',
            'response': {'demo': True}
        }
    
    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": components
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message_id': response_data.get('messages', [{}])[0].get('id', ''),
                'response': response_data
            }
        else:
            return {
                'success': False,
                'error': response_data.get('error', {}).get('message', 'Unknown error'),
                'response': response_data
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response': None
        }


def test_whatsapp_connection(test_phone_number="919876543210"):
    """
    Test if WhatsApp API is working
    """
    test_message = "Test message from Do Auto Review System - Hello! This is a test."
    
    result = send_whatsapp_message(test_phone_number, test_message)
    
    if result['success']:
        print("✅ WhatsApp API is working!")
        print(f"Message ID: {result['message_id']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    return result