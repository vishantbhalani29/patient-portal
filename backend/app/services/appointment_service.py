from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, AppointmentStatus

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
                scheduled_start=None,
                scheduled_end=None,
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
