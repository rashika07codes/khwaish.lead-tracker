import requests
from fastapi.templating import Jinja2Templates
from datetime import datetime
from . import models, config

# Templates are loaded from the main app
templates = Jinja2Templates(directory="app/templates")

def _render_email_content(lead: models.Lead, kind: str) -> dict:
    """Renders the email subject and HTML body based on the kind (first or reminder)."""
    
    # The reply link hits the API endpoint to mark the lead as replied
    reply_link = f"{config.settings.APP_BASE_URL}/api/leads/{lead.id}/mark-replied"
    
    if kind == "first":
        subject = f"Thanks for reaching out, {lead.name} — KHWAISH"
        template_name = "email_first.html"
    elif kind == "reminder":
        subject = f"Quick follow-up, {lead.name} — KHWAISH"
        template_name = "email_reminder.html"
    else:
        raise ValueError("Invalid email kind")

    context = {
        "lead": lead,
        "reply_link": reply_link,
        "base_url": config.settings.APP_BASE_URL,
        "current_year": datetime.now().year
    }
    
    # Render the HTML body
    html_body = templates.get_template(template_name).render(context)
    
    return {"subject": subject, "html_body": html_body}

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    MOCK function for sending email.
    In a real application, this would use the Gmail API or SMTP.
    """
    print(f"\n--- MOCK EMAIL SENT ---")
    print(f"TO: {to_email}")
    print(f"FROM: {config.settings.FROM_EMAIL}")
    print(f"SUBJECT: {subject}")
    print(f"BODY (Snippet):\n{html_body[:200]}...")
    print(f"-----------------------\n")
    
    # Assume success for the mock
    return True

def send_first_contact_email(lead: models.Lead) -> bool:
    """Sends the initial contact email to the lead."""
    try:
        content = _render_email_content(lead, "first")
        return _send_email(lead.email, content["subject"], content["html_body"])
    except Exception as e:
        print(f"Error sending first contact email to {lead.email}: {e}")
        return False

def send_reminder_email(lead: models.Lead) -> bool:
    """Sends the reminder email to the lead."""
    try:
        content = _render_email_content(lead, "reminder")
        return _send_email(lead.email, content["subject"], content["html_body"])
    except Exception as e:
        print(f"Error sending reminder email to {lead.email}: {e}")
        return False
