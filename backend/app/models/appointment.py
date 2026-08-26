from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, Index
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Appointment(Base):
    """
    Appointment entity representing patient portal appointments.
    Note: Standard appointment duration for scheduled appointments is fixed at 30 minutes for this assignment.
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    patient_name = Column(String, nullable=False)
    patient_email = Column(String, nullable=False)
    provider_id = Column(String, nullable=False, index=True)
    provider_name = Column(String, nullable=False)
    appointment_type = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    
    requested_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(SQLEnum(AppointmentStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=AppointmentStatus.PENDING)
    version = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        Index("idx_provider_status_start", "provider_id", "status", "scheduled_start"),
        Index("idx_patient_status_start", "patient_id", "status", "scheduled_start"),
    )
