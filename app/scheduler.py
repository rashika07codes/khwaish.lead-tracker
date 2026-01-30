from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, crud
from .db import SessionLocal
from .email_service import send_reminder_email
from .whatsapp_service import trigger_whatsapp_message

scheduler = BackgroundScheduler()

def check_for_reminders():
    """
    Scheduler job that checks for leads needing a 3-day reminder.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running reminder check job...")
    
    db: Session = SessionLocal()
    try:
        three_days_ago = datetime.utcnow() - timedelta(days=3)
        
        # Find leads that were contacted 3+ days ago, have not replied, and are not already reminded
        leads_to_remind = db.query(models.Lead).filter(
            models.Lead.status == models.LeadStatus.CONTACTED,
            models.Lead.replied_at.is_(None),
            models.Lead.first_contact_at <= three_days_ago
        ).all()
        
        print(f"Found {len(leads_to_remind)} leads requiring a reminder.")
        
        for lead in leads_to_remind:
            print(f"Processing reminder for Lead ID: {lead.id}, Name: {lead.name}")
            
            # 1. Send Reminder Email
            email_success = send_reminder_email(lead)
            
            # 2. Trigger WhatsApp Reminder
            whatsapp_success = trigger_whatsapp_message(lead, "REMINDER")
            
            # 3. Update DB
            lead.status = models.LeadStatus.REMINDER_SENT
            lead.reminder_sent_at = datetime.utcnow()
            lead.last_touch_at = datetime.utcnow()
            
            # 4. Log messages
            crud.log_message(db, lead.id, "EMAIL", "REMINDER", email_success, "Reminder email sent successfully" if email_success else "Reminder email failed")
            crud.log_message(db, lead.id, "WHATSAPP", "REMINDER", whatsapp_success, "Reminder WhatsApp triggered successfully" if whatsapp_success else "Reminder WhatsApp trigger failed")
            
            db.commit()
            
    except Exception as e:
        print(f"An error occurred during the reminder check: {e}")
        db.rollback()
    finally:
        db.close()
        print("Reminder check job finished.")

def start_scheduler():
    """Starts the background scheduler."""
    if not scheduler.running:
        # Schedule the job to run every hour
        scheduler.add_job(check_for_reminders, 'interval', hours=1, id='reminder_check_job')
        scheduler.start()
        print("APScheduler started and job scheduled to run every hour.")

def schedule_reminder_check():
    """
    This function is called by main.py on startup to ensure the job is scheduled.
    It is also the function to be called by the CLI command.
    """
    # If running standalone (e.g., via CLI), we just run the check once.
    # If running within the FastAPI app, the scheduler is started.
    if not scheduler.running:
        check_for_reminders()
