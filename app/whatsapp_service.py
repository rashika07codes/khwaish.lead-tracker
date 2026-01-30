import requests
from . import models, config

def trigger_whatsapp_message(lead: models.Lead, kind: str) -> bool:
    """
    Triggers a webhook to Make.com or Zapier to send a WhatsApp message.
    
    Args:
        lead: The lead object.
        kind: "FIRST_TOUCH" or "REMINDER".
        
    Returns:
        True if the webhook was successfully called, False otherwise.
    """
    webhook_url = config.settings.MAKE_ZAPIER_WEBHOOK_URL
    
    if not webhook_url:
        print("WARNING: MAKE_ZAPIER_WEBHOOK_URL is not set. Skipping WhatsApp trigger.")
        return False
        
    payload = {
        "lead_id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "type": kind,
        "message": f"Hello {lead.name}, this is a {kind.lower().replace('_', ' ')} message from KHWAISH."
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        print(f"WhatsApp webhook successfully triggered for lead {lead.id} ({kind}). Response: {response.status_code}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to trigger WhatsApp webhook for lead {lead.id} ({kind}). Error: {e}")
        return False
