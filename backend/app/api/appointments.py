from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.appointment import AppointmentResponse
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
