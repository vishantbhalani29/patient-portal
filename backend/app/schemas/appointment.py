from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.appointment import AppointmentStatus

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    patient_name: str
    patient_email: str
    provider_id: str
    provider_name: str
    appointment_type: str
    reason: Optional[str] = None
    requested_start: datetime
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: AppointmentStatus
    version: int
    created_at: datetime
    updated_at: datetime

class AppointmentCreateRequest(BaseModel):
    patient_id: str
    patient_name: str
    patient_email: str
    provider_id: str
    provider_name: str
    appointment_type: str = Field(default="General Consultation")
    reason: Optional[str] = None
    requested_start: datetime

class AppointmentConfirmRequest(BaseModel):
    expected_version: int
    scheduled_start: Optional[datetime] = None
    actor_id: Optional[str] = None
    actor_role: Optional[str] = "provider"

class AppointmentRescheduleRequest(BaseModel):
    expected_version: int
    scheduled_start: Optional[datetime] = None
    new_start: Optional[datetime] = None
    actor_id: Optional[str] = None
    actor_role: Optional[str] = "provider"

    @property
    def target_start(self) -> Optional[datetime]:
        return self.scheduled_start or self.new_start

class AppointmentCancelRequest(BaseModel):
    expected_version: int
    actor_id: Optional[str] = None
    actor_role: Optional[str] = "patient"
