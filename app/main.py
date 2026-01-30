import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from . import models, schemas, crud, config
from .db import SessionLocal, engine
from .email_service import send_first_contact_email, send_reminder_email
from .whatsapp_service import trigger_whatsapp_message
from .scheduler import start_scheduler, schedule_reminder_check

# --- Configuration and Initialization ---
config.load_config()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KHWAISH Lead Follow-Up Automation System",
    description="A system to automate lead follow-up via Email and WhatsApp.",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Startup and Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    print("Starting scheduler...")
    start_scheduler()
    schedule_reminder_check()

@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down...")

# --- API Endpoints ---

@app.post("/api/leads", response_model=schemas.Lead)
def create_lead_api(lead_in: schemas.LeadCreate, db: Session = Depends(get_db)):
    """
    Endpoint to create a new lead (e.g., from a web form).
    Triggers the initial contact automation.
    """
    db_lead = crud.create_lead(db=db, lead=lead_in)
    
    # --- Automation Flow A: Initial Contact ---
    
    # 1. Send Email
    email_success = send_first_contact_email(db_lead)
    
    # 2. Trigger WhatsApp
    whatsapp_success = trigger_whatsapp_message(db_lead, "FIRST_TOUCH")
    
    # 3. Update DB
    db_lead.status = models.LeadStatus.CONTACTED
    db_lead.first_contact_at = datetime.utcnow()
    db_lead.email_sent_at = datetime.utcnow() if email_success else None
    db_lead.whatsapp_sent_at = datetime.utcnow() if whatsapp_success else None
    db_lead.last_touch_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_lead)
    
    # Log messages (simplified for now, full logging in crud)
    crud.log_message(db, db_lead.id, "EMAIL", "FIRST_TOUCH", email_success, "Email sent successfully" if email_success else "Email failed")
    crud.log_message(db, db_lead.id, "WHATSAPP", "FIRST_TOUCH", whatsapp_success, "WhatsApp triggered successfully" if whatsapp_success else "WhatsApp trigger failed")
    
    return db_lead

@app.post("/api/leads/import-csv", response_model=list[schemas.Lead])
async def import_csv(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to import leads from a CSV file.
    NOTE: This is a simplified implementation. In a real app, you'd parse the file.
    For now, it expects a multipart form data with a 'file' field.
    """
    form = await request.form()
    csv_file = form.get("file")
    
    if not csv_file:
        raise HTTPException(status_code=400, detail="No file provided")

    # Read the file content (assuming simple CSV: name,email,phone,source)
    content = await csv_file.read()
    content_str = content.decode('utf-8')
    
    imported_leads = []
    # Skip header row
    for line in content_str.strip().split('\n')[1:]:
        parts = line.split(',')
        if len(parts) >= 4:
            lead_in = schemas.LeadCreate(
                name=parts[0].strip(),
                email=parts[1].strip(),
                phone=parts[2].strip(),
                source=parts[3].strip(),
                message=parts[4].strip() if len(parts) > 4 else None
            )
            db_lead = crud.create_lead(db=db, lead=lead_in)
            
            # Trigger automation (same as create_lead_api)
            email_success = send_first_contact_email(db_lead)
            whatsapp_success = trigger_whatsapp_message(db_lead, "FIRST_TOUCH")
            
            db_lead.status = models.LeadStatus.CONTACTED
            db_lead.first_contact_at = datetime.utcnow()
            db_lead.email_sent_at = datetime.utcnow() if email_success else None
            db_lead.whatsapp_sent_at = datetime.utcnow() if whatsapp_success else None
            db_lead.last_touch_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_lead)
            
            crud.log_message(db, db_lead.id, "EMAIL", "FIRST_TOUCH", email_success, "Email sent successfully" if email_success else "Email failed")
            crud.log_message(db, db_lead.id, "WHATSAPP", "FIRST_TOUCH", whatsapp_success, "WhatsApp triggered successfully" if whatsapp_success else "WhatsApp trigger failed")
            
            imported_leads.append(db_lead)
            
    return imported_leads

@app.get("/api/leads", response_model=list[schemas.Lead])
def list_leads(
    status: models.LeadStatus | None = None,
    source: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List leads with optional filtering."""
    return crud.get_leads(db, status=status, source=source, skip=skip, limit=limit)

@app.get("/api/leads/{lead_id}", response_model=schemas.Lead)
def get_lead_detail(lead_id: int, db: Session = Depends(get_db)):
    """Get details for a specific lead."""
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead

@app.post("/api/leads/{lead_id}/mark-replied", response_model=schemas.Lead)
def mark_lead_replied(lead_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to manually mark a lead as replied, or hit by the 'reply link' in the email.
    """
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if db_lead.status not in [models.LeadStatus.REPLIED, models.LeadStatus.WON, models.LeadStatus.LOST]:
        db_lead.status = models.LeadStatus.REPLIED
        db_lead.replied_at = datetime.utcnow()
        db_lead.last_touch_at = datetime.utcnow()
        db.commit()
        db.refresh(db_lead)
        
    return db_lead

@app.post("/api/leads/{lead_id}/send-reminder", response_model=schemas.Lead)
def send_manual_reminder(lead_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to manually send a reminder email and WhatsApp message.
    """
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Send Email
    email_success = send_reminder_email(db_lead)
    
    # Trigger WhatsApp
    whatsapp_success = trigger_whatsapp_message(db_lead, "REMINDER")
    
    # Update DB
    db_lead.status = models.LeadStatus.REMINDER_SENT
    db_lead.reminder_sent_at = datetime.utcnow()
    db_lead.last_touch_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_lead)
    
    # Log messages
    crud.log_message(db, db_lead.id, "EMAIL", "REMINDER", email_success, "Reminder email sent successfully" if email_success else "Reminder email failed")
    crud.log_message(db, db_lead.id, "WHATSAPP", "REMINDER", whatsapp_success, "Reminder WhatsApp triggered successfully" if whatsapp_success else "Reminder WhatsApp trigger failed")
    
    return db_lead

@app.post("/api/leads/{lead_id}/update-status", response_model=schemas.Lead)
def update_lead_status(lead_id: int, status_update: schemas.LeadStatusUpdate, db: Session = Depends(get_db)):
    """
    Endpoint to manually update a lead's status (WON/LOST/IN_PROGRESS).
    """
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db_lead.status = status_update.status
    db_lead.last_touch_at = datetime.utcnow()
    db.commit()
    db.refresh(db_lead)
    
    return db_lead

@app.get("/api/kpis")
def get_kpis(db: Session = Depends(get_db)):
    """Calculate and return key performance indicators."""
    total_leads = db.query(models.Lead).count()
    contacted = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.CONTACTED).count()
    replied = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.REPLIED).count()
    reminders_sent = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.REMINDER_SENT).count()
    won = db.query(models.Lead).filter(models.Lead.status == models.LeadStatus.WON).count()
    
    conversion_rate = (won / total_leads) * 100 if total_leads > 0 else 0
    
    return {
        "total_leads": total_leads,
        "contacted": contacted,
        "replied": replied,
        "reminders_sent": reminders_sent,
        "won": won,
        "conversion_rate": f"{conversion_rate:.2f}%"
    }

# --- Web Dashboard Endpoints ---

@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard page with KPIs and leads table."""
    kpis = get_kpis(db)
    leads = crud.get_leads(db, limit=20) # Show top 20 for dashboard view
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "kpis": kpis, "leads": leads, "statuses": [s.value for s in models.LeadStatus]}
    )

@app.get("/lead/{lead_id}")
def lead_detail_page(request: Request, lead_id: int, db: Session = Depends(get_db)):
    """Lead detail page showing timeline and actions."""
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    messages = crud.get_message_logs_for_lead(db, lead_id=lead_id)
    
    return templates.TemplateResponse(
        "lead_detail.html",
        {"request": request, "lead": db_lead, "messages": messages, "statuses": [s.value for s in models.LeadStatus]}
    )

# --- Webhook Endpoints (Placeholder) ---

@app.post("/webhooks/whatsapp-status")
def whatsapp_status_webhook(status_update: schemas.WhatsAppStatusUpdate, db: Session = Depends(get_db)):
    """
    Webhook to receive delivery status updates from WhatsApp provider (via Make/Zapier).
    """
    # In a real application, you would parse the payload and update the MessageLog
    print(f"Received WhatsApp status update for lead {status_update.lead_id}: {status_update.status}")
    
    # Example: update MessageLog success status
    # crud.update_message_log_status(db, status_update.message_id, status_update.status == "delivered")
    
    return {"message": "Status received"}

# --- CLI for Scheduler (for external cron/systemd) ---
if __name__ == "__main__":
    # This block is for running the scheduler as a standalone process
    # The main app will run the scheduler on startup
    # This is a placeholder for the requested CLI: `python -m khwaish.run_scheduler`
    # The actual scheduler logic is in app/scheduler.py
    print("Running KHWAISH scheduler check...")
    schedule_reminder_check()
    print("Scheduler check complete.")
