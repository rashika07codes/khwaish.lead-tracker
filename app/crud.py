from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from . import models, schemas

# --- Lead CRUD Operations ---

def get_lead(db: Session, lead_id: int):
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()

def get_leads(db: Session, status: models.LeadStatus | None = None, source: str | None = None, skip: int = 0, limit: int = 100) -> List[models.Lead]:
    query = db.query(models.Lead)
    if status:
        query = query.filter(models.Lead.status == status)
    if source:
        query = query.filter(models.Lead.source == source)
    return query.offset(skip).limit(limit).all()

def create_lead(db: Session, lead: schemas.LeadCreate):
    db_lead = models.Lead(
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        message=lead.message,
        status=models.LeadStatus.NEW,
        created_at=datetime.utcnow(),
        last_touch_at=datetime.utcnow()
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

# --- MessageLog CRUD Operations ---

def log_message(db: Session, lead_id: int, channel: str, kind: str, success: bool, provider_response: str | None = None):
    db_log = models.MessageLog(
        lead_id=lead_id,
        channel=models.MessageChannel(channel),
        kind=models.MessageKind(kind),
        success=success,
        provider_response=provider_response,
        sent_at=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_message_logs_for_lead(db: Session, lead_id: int) -> List[models.MessageLog]:
    return db.query(models.MessageLog).filter(models.MessageLog.lead_id == lead_id).order_by(models.MessageLog.sent_at.desc()).all()
