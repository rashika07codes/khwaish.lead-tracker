from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from .models import LeadStatus, MessageChannel, MessageKind

# --- Lead Schemas ---

class LeadBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    source: str
    message: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadStatusUpdate(BaseModel):
    status: LeadStatus

class Lead(LeadBase):
    id: int
    status: LeadStatus
    created_at: datetime
    first_contact_at: Optional[datetime] = None
    email_thread_id: Optional[str] = None
    email_sent_at: Optional[datetime] = None
    whatsapp_sent_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    reminder_sent_at: Optional[datetime] = None
    last_touch_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True
        use_enum_values = True

# --- MessageLog Schemas ---

class MessageLogBase(BaseModel):
    lead_id: int
    channel: MessageChannel
    kind: MessageKind
    provider_response: Optional[str] = None
    success: bool

class MessageLogCreate(MessageLogBase):
    pass

class MessageLog(MessageLogBase):
    id: int
    sent_at: datetime

    class Config:
        orm_mode = True
        use_enum_values = True

# --- Webhook Schemas ---

class WhatsAppStatusUpdate(BaseModel):
    lead_id: int
    message_id: str
    status: str # e.g., "delivered", "read", "failed"
