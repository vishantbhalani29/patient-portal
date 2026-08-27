import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_event import AuditEvent
from app.schemas.appointment import (
    AppointmentCreateRequest,
    AppointmentConfirmRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
)
from app.exceptions import StaleAppointmentException, ProviderScheduleConflictException

class AppointmentService:
    @staticmethod
    def _capture_snapshot(appointment: Appointment) -> dict:
        """
        Captures a clean business state snapshot of an appointment.
        """
        if not appointment:
            return None
        return {
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "patient_name": appointment.patient_name,
            "patient_email": appointment.patient_email,
            "provider_id": appointment.provider_id,
            "provider_name": appointment.provider_name,
            "appointment_type": appointment.appointment_type,
            "reason": appointment.reason,
            "requested_start": appointment.requested_start.isoformat() if appointment.requested_start else None,
            "scheduled_start": appointment.scheduled_start.isoformat() if appointment.scheduled_start else None,
            "scheduled_end": appointment.scheduled_end.isoformat() if appointment.scheduled_end else None,
            "status": appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status),
            "version": appointment.version,
        }

    @staticmethod
    def _log_audit_event(
        db: Session,
        appointment_id: int,
        actor_id: str,
        actor_role: str,
        action: str,
        before_state: Optional[dict],
        after_state: dict,
    ) -> AuditEvent:
        """
        Inserts an append-only audit event record into the session.
        Must be committed within the parent transaction.
        """
        audit_event = AuditEvent(
            appointment_id=appointment_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            before_state=json.dumps(before_state) if before_state else None,
            after_state=json.dumps(after_state) if after_state else None,
        )
        db.add(audit_event)
        return audit_event

    @staticmethod
    def _verify_version(appointment: Appointment, expected_version: int) -> None:
        """
        Reusable helper to verify optimistic concurrency control version.
        Raises StaleAppointmentException (HTTP 409) if versions mismatch.
        """
        if appointment.version != expected_version:
            raise StaleAppointmentException(current_version=appointment.version)

    @staticmethod
    def _validate_provider_availability(
        db: Session,
        provider_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: int,
    ) -> None:
        """
        Validates that a provider has no overlapping CONFIRMED appointments.
        Overlap condition: new_start < existing_end AND new_end > existing_start.
        Raises ProviderScheduleConflictException (HTTP 409) if an overlap exists.
        """
        conflict = (
            db.query(Appointment)
            .filter(
                Appointment.provider_id == provider_id,
                Appointment.status == AppointmentStatus.CONFIRMED,
                Appointment.id != exclude_appointment_id,
                Appointment.scheduled_start < end_time,
                Appointment.scheduled_end > start_time,
            )
            .first()
        )

        if conflict:
            raise ProviderScheduleConflictException()

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
    def get_appointment_history(db: Session, appointment_id: int) -> List[AuditEvent]:
        # Raises 404 if appointment doesn't exist
        AppointmentService.get_appointment_by_id(db, appointment_id)
        return (
            db.query(AuditEvent)
            .filter(AuditEvent.appointment_id == appointment_id)
            .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
            .all()
        )

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
        db.flush()  # Flush to generate appointment.id for audit event foreign key

        after_state = AppointmentService._capture_snapshot(appointment)
        AppointmentService._log_audit_event(
            db=db,
            appointment_id=appointment.id,
            actor_id=request.patient_id,
            actor_role="patient",
            action="request",
            before_state=None,
            after_state=after_state,
        )

        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def confirm_appointment(
        db: Session, appointment_id: int, request: AppointmentConfirmRequest
    ) -> Appointment:
        # 1. Load appointment
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        # 2. Validate version
        AppointmentService._verify_version(appointment, request.expected_version)
        
        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(status_code=400, detail="Only pending appointments can be confirmed.")
        
        target_start = request.scheduled_start or appointment.scheduled_start or appointment.requested_start
        target_end = target_start + timedelta(minutes=30)

        # 3. Validate provider availability
        AppointmentService._validate_provider_availability(
            db=db,
            provider_id=appointment.provider_id,
            start_time=target_start,
            end_time=target_end,
            exclude_appointment_id=appointment.id,
        )

        # 4. Capture before_state
        before_state = AppointmentService._capture_snapshot(appointment)

        # 5. Apply mutation & 6. Increment version
        appointment.scheduled_start = target_start
        appointment.scheduled_end = target_end
        appointment.status = AppointmentStatus.CONFIRMED
        appointment.version += 1
        appointment.updated_at = datetime.now(timezone.utc)
        
        # 7. Capture after_state & Create audit event
        after_state = AppointmentService._capture_snapshot(appointment)
        actor_id = request.actor_id or appointment.provider_id
        actor_role = request.actor_role or "provider"
        
        AppointmentService._log_audit_event(
            db=db,
            appointment_id=appointment.id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="confirm",
            before_state=before_state,
            after_state=after_state,
        )

        # 8. Commit
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def reschedule_appointment(
        db: Session, appointment_id: int, request: AppointmentRescheduleRequest
    ) -> Appointment:
        # 1. Load appointment
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        # 2. Validate version
        AppointmentService._verify_version(appointment, request.expected_version)
        
        target_start = request.target_start
        if not target_start:
            raise HTTPException(status_code=400, detail="scheduled_start is required for rescheduling.")

        target_end = target_start + timedelta(minutes=30)

        # 3. Validate provider availability
        AppointmentService._validate_provider_availability(
            db=db,
            provider_id=appointment.provider_id,
            start_time=target_start,
            end_time=target_end,
            exclude_appointment_id=appointment.id,
        )

        # 4. Capture before_state
        before_state = AppointmentService._capture_snapshot(appointment)

        # 5. Apply mutation & 6. Increment version
        appointment.scheduled_start = target_start
        appointment.scheduled_end = target_end
        appointment.version += 1
        appointment.updated_at = datetime.now(timezone.utc)
        
        # 7. Capture after_state & Create audit event
        after_state = AppointmentService._capture_snapshot(appointment)
        actor_id = request.actor_id or appointment.provider_id
        actor_role = request.actor_role or "provider"

        AppointmentService._log_audit_event(
            db=db,
            appointment_id=appointment.id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="reschedule",
            before_state=before_state,
            after_state=after_state,
        )

        # 8. Commit
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(
        db: Session, appointment_id: int, request: AppointmentCancelRequest
    ) -> Appointment:
        # 1. Load appointment
        appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
        
        # 2. Validate version
        AppointmentService._verify_version(appointment, request.expected_version)
        
        if appointment.status != AppointmentStatus.CONFIRMED:
            raise HTTPException(status_code=400, detail="Only confirmed appointments can be cancelled.")
        
        # Capture before_state
        before_state = AppointmentService._capture_snapshot(appointment)

        # Apply mutation & Increment version
        appointment.status = AppointmentStatus.CANCELLED
        appointment.version += 1
        appointment.updated_at = datetime.now(timezone.utc)
        
        # Capture after_state & Create audit event
        after_state = AppointmentService._capture_snapshot(appointment)
        actor_id = request.actor_id or appointment.patient_id
        actor_role = request.actor_role or "patient"

        AppointmentService._log_audit_event(
            db=db,
            appointment_id=appointment.id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="cancel",
            before_state=before_state,
            after_state=after_state,
        )

        # Commit
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def seed_data(db: Session) -> None:
        """
        Idempotent database seeding for original demo data with initial audit events.
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
        db.flush()

        for appt in seed_appointments:
            snapshot = AppointmentService._capture_snapshot(appt)
            AppointmentService._log_audit_event(
                db=db,
                appointment_id=appt.id,
                actor_id=appt.patient_id,
                actor_role="patient",
                action="request",
                before_state=None,
                after_state=snapshot,
            )

        db.commit()
