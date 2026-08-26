from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AuditEvent(Base):
    """
    Append-only audit trail event tracking history of appointment changes.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    actor_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)  # "patient" | "provider" | "system"
    action = Column(String, nullable=False)       # "request" | "confirm" | "reschedule" | "cancel"
    before_state = Column(Text, nullable=True)   # JSON string snapshot of state before change
    after_state = Column(Text, nullable=True)    # JSON string snapshot of state after change
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
