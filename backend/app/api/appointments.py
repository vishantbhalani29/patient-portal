from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.appointment import (
    AppointmentResponse,
    AppointmentCreateRequest,
    AppointmentConfirmRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()

@router.get("/appointments", response_model=List[AppointmentResponse])
def get_appointments(
    role: Optional[str] = Query(None, description="Role filter: patient or provider"),
    user_id: Optional[str] = Query(None, description="ID of patient or provider"),
    db: Session = Depends(get_db),
):
    """
    List appointments with optional role and user_id filtering.
    """
    return AppointmentService.get_appointments(db=db, role=role, user_id=user_id)

@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    request: AppointmentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new appointment request (starts as PENDING).
    """
    return AppointmentService.create_appointment(db=db, request=request)

@router.post("/appointments/{id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(
    id: int,
    request: AppointmentConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm a pending appointment.
    """
    return AppointmentService.confirm_appointment(db=db, appointment_id=id, request=request)

@router.post("/appointments/{id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    id: int,
    request: AppointmentRescheduleRequest,
    db: Session = Depends(get_db),
):
    """
    Reschedule an appointment.
    """
    return AppointmentService.reschedule_appointment(db=db, appointment_id=id, request=request)

@router.post("/appointments/{id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    id: int,
    request: AppointmentCancelRequest,
    db: Session = Depends(get_db),
):
    """
    Cancel a confirmed appointment.
    """
    return AppointmentService.cancel_appointment(db=db, appointment_id=id, request=request)
