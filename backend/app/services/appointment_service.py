from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentConfirmRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
)

class AppointmentService:
    @staticmethod
    def get_appointments(db: Session, role: Optional[str] = None, user_id: Optional[str] = None) -> List[Appointment]:
        query = db.query(Appointment)
        if role == "patient" and user_id:
            query = query.filter(Appointment.patient_id == user_id)
        elif role == "provider" and user_id:
            query = query.filter(Appointment.provider_id == user_id)
        return query.order_by(Appointment.created_at.desc()).all()

    @staticmethod
    def get_appointment_by_id(db: Session, appointment_id: int) -> Appointment:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment

    @staticmethod
    def create_appointment(db: Session, request: AppointmentCreateRequest) -> Appointment:
        scheduled_start = request.requested_start
        scheduled_end = scheduled_start + timedelta(minutes=30)
        
        appointment = Appointment(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            patient_email=request.patient_email,
            provider_id=request.provider_id,
            provider_name=request.provider_name,
            appointment_type=request.appointment_type,
            reason=request.reason,
            requested_start=request.requested_start,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            status=AppointmentStatus.PENDING,
            version=1,
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def confirm_appointment(
        db: Session, appointment_id: int, request: Optional[AppointmentConfirmRequest] = None
    ) -> Appointment:
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(status_code=400, detail="Only pending appointments can be confirmed.")
        
        if request and request.scheduled_start:
            appointment.scheduled_start = request.scheduled_start
            appointment.scheduled_end = request.scheduled_start + timedelta(minutes=30)
        elif not appointment.scheduled_start:
            appointment.scheduled_start = appointment.requested_start
            appointment.scheduled_end = appointment.requested_start + timedelta(minutes=30)

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def reschedule_appointment(
        db: Session, appointment_id: int, request: AppointmentRescheduleRequest
    ) -> Appointment:
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        target_start = request.target_start
        if not target_start:
            raise HTTPException(status_code=400, detail="scheduled_start is required for rescheduling.")

        appointment.scheduled_start = target_start
        appointment.scheduled_end = target_start + timedelta(minutes=30)
        appointment.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(
        db: Session, appointment_id: int, request: Optional[AppointmentCancelRequest] = None
    ) -> Appointment:
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        if appointment.status != AppointmentStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Only confirmed appointments can be cancelled.")
        
        appointment.status = AppointmentStatus.CANCELLED
        appointment.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def seed_data(db: Session) -> None:
        """
        Idempotent database seeding for original demo data.
        """
        if db.query(Appointment).first() is not None:
            return  # Seed data already exists

        # Seed data with original demo records for Olivia Carter & Dr. Ethan Brooks
        seed_appointments = [
            Appointment(
                patient_id="patient-001",
                patient_name="Olivia Carter",
                patient_email="olivia.carter@email.test",
                provider_id="provider-001",
                provider_name="Dr. Ethan Brooks",
                appointment_type="Behavioral Health Intake",
                reason="Initial behavioral health intake assessment.",
                requested_start=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
                scheduled_start=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
                scheduled_end=datetime(2026, 9, 1, 10, 30, 0, tzinfo=timezone.utc),
                status=AppointmentStatus.CONFIRMED,
                version=1,
            ),
            Appointment(
                patient_id="patient-001",
                patient_name="Olivia Carter",
                patient_email="olivia.carter@email.test",
                provider_id="provider-001",
                provider_name="Dr. Ethan Brooks",
                appointment_type="Medication Review",
                reason="Follow-up on current prescription dosage.",
                requested_start=datetime(2026, 9, 2, 14, 0, 0, tzinfo=timezone.utc),
                scheduled_start=datetime(2026, 9, 2, 14, 0, 0, tzinfo=timezone.utc),
                scheduled_end=datetime(2026, 9, 2, 14, 30, 0, tzinfo=timezone.utc),
                status=AppointmentStatus.PENDING,
                version=1,
            ),
            Appointment(
                patient_id="patient-001",
                patient_name="Olivia Carter",
                patient_email="olivia.carter@email.test",
                provider_id="provider-001",
                provider_name="Dr. Ethan Brooks",
                appointment_type="Counseling Session",
                reason="Bi-weekly progress check-in.",
                requested_start=datetime(2026, 9, 3, 11, 0, 0, tzinfo=timezone.utc),
                scheduled_start=datetime(2026, 9, 3, 11, 0, 0, tzinfo=timezone.utc),
                scheduled_end=datetime(2026, 9, 3, 11, 30, 0, tzinfo=timezone.utc),
                status=AppointmentStatus.CONFIRMED,
                version=1,
            ),
        ]

        db.add_all(seed_appointments)
        db.commit()
