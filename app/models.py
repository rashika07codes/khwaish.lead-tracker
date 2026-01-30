from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from .db import Base

class LeadStatus(PyEnum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    REMINDER_SENT = "REMINDER_SENT"
    IN_PROGRESS = "IN_PROGRESS"
    WON = "WON"
    LOST = "LOST"

class MessageChannel(PyEnum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"

class MessageKind(PyEnum):
    FIRST_TOUCH = "FIRST_TOUCH"
    REMINDER = "REMINDER"
    MANUAL = "MANUAL"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True, nullable=True)
    source = Column(String)
    message = Column(String, nullable=True)
    
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    first_contact_at = Column(DateTime(timezone=True), nullable=True)
    email_thread_id = Column(String, nullable=True)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    whatsapp_sent_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_touch_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    
    # Relationship to MessageLog
    messages = relationship("MessageLog", back_populates="lead")

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    
    channel = Column(Enum(MessageChannel))
    kind = Column(Enum(MessageKind))
    
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    provider_response = Column(String, nullable=True)
    success = Column(Boolean, default=False)
    
    # Relationship to Lead
    lead = relationship("Lead", back_populates="messages")
