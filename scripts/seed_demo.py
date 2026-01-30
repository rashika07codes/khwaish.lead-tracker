import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app import crud, schemas, models
from app.config import load_config

def seed_demo_data():
    """Creates 10 leads with mixed statuses for demonstration."""
    load_config()
    db = SessionLocal()
    
    try:
        print("Seeding demo data...")
        
        # Lead 1: NEW (Should be contacted on startup)
        lead1 = schemas.LeadCreate(name="Alice Johnson", email="alice.j@example.com", phone="123-456-7890", source="website", message="Interested in pricing.")
        crud.create_lead(db, lead1)
        
        # Lead 2: CONTACTED (Contacted 1 day ago, waiting for reply)
        lead2_data = schemas.LeadCreate(name="Bob Smith", email="bob.s@example.com", phone="987-654-3210", source="facebook", message="Saw your ad.")
        lead2 = crud.create_lead(db, lead2_data)
        lead2.status = models.LeadStatus.CONTACTED
        lead2.first_contact_at = datetime.utcnow() - timedelta(days=1)
        lead2.email_sent_at = lead2.first_contact_at
        lead2.whatsapp_sent_at = lead2.first_contact_at
        crud.log_message(db, lead2.id, "EMAIL", "FIRST_TOUCH", True, "Mock sent")
        crud.log_message(db, lead2.id, "WHATSAPP", "FIRST_TOUCH", True, "Mock triggered")
        
        # Lead 3: REMINDER_SENT (Contacted 4 days ago, reminded 1 day ago)
        lead3_data = schemas.LeadCreate(name="Charlie Brown", email="charlie.b@example.com", phone="555-123-4567", source="referral", message="Referred by a friend.")
        lead3 = crud.create_lead(db, lead3_data)
        lead3.status = models.LeadStatus.REMINDER_SENT
        lead3.first_contact_at = datetime.utcnow() - timedelta(days=4)
        lead3.email_sent_at = lead3.first_contact_at
        lead3.whatsapp_sent_at = lead3.first_contact_at
        lead3.reminder_sent_at = datetime.utcnow() - timedelta(days=1)
        crud.log_message(db, lead3.id, "EMAIL", "FIRST_TOUCH", True, "Mock sent")
        crud.log_message(db, lead3.id, "WHATSAPP", "FIRST_TOUCH", True, "Mock triggered")
        crud.log_message(db, lead3.id, "EMAIL", "REMINDER", True, "Mock sent")
        crud.log_message(db, lead3.id, "WHATSAPP", "REMINDER", True, "Mock triggered")
        
        # Lead 4: REPLIED (Replied 2 days ago)
        lead4_data = schemas.LeadCreate(name="Diana Prince", email="diana.p@example.com", phone="111-222-3333", source="website", message="Ready to buy.")
        lead4 = crud.create_lead(db, lead4_data)
        lead4.status = models.LeadStatus.REPLIED
        lead4.first_contact_at = datetime.utcnow() - timedelta(days=5)
        lead4.replied_at = datetime.utcnow() - timedelta(days=2)
        crud.log_message(db, lead4.id, "EMAIL", "FIRST_TOUCH", True, "Mock sent")
        
        # Lead 5: WON
        lead5_data = schemas.LeadCreate(name="Ethan Hunt", email="ethan.h@example.com", phone="444-555-6666", source="referral", message="Closed the deal.")
        lead5 = crud.create_lead(db, lead5_data)
        lead5.status = models.LeadStatus.WON
        lead5.first_contact_at = datetime.utcnow() - timedelta(days=10)
        lead5.replied_at = datetime.utcnow() - timedelta(days=8)
        
        # Lead 6: LOST
        lead6_data = schemas.LeadCreate(name="Fiona Glenanne", email="fiona.g@example.com", phone="777-888-9999", source="facebook", message="Lost to competitor.")
        lead6 = crud.create_lead(db, lead6_data)
        lead6.status = models.LeadStatus.LOST
        lead6.first_contact_at = datetime.utcnow() - timedelta(days=7)
        
        # Lead 7: CONTACTED (Contacted 3 days ago, should be reminded by scheduler)
        lead7_data = schemas.LeadCreate(name="George Lucas", email="george.l@example.com", phone="000-111-2222", source="website", message="Testing reminder logic.")
        lead7 = crud.create_lead(db, lead7_data)
        lead7.status = models.LeadStatus.CONTACTED
        lead7.first_contact_at = datetime.utcnow() - timedelta(days=3, hours=1) # Just over 3 days
        lead7.email_sent_at = lead7.first_contact_at
        crud.log_message(db, lead7.id, "EMAIL", "FIRST_TOUCH", True, "Mock sent")
        
        # Lead 8, 9, 10: NEW
        crud.create_lead(db, schemas.LeadCreate(name="Hannah Montana", email="hannah.m@example.com", phone="123-000-4567", source="website", message="New lead 8"))
        crud.create_lead(db, schemas.LeadCreate(name="Ian Malcolm", email="ian.m@example.com", phone="987-111-6543", source="referral", message="New lead 9"))
        crud.create_lead(db, schemas.LeadCreate(name="Jane Doe", email="jane.d@example.com", phone="555-222-1234", source="facebook", message="New lead 10"))
        
        db.commit()
        print("Demo data seeding complete. 10 leads created.")
        
    except Exception as e:
        print(f"An error occurred during data seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
