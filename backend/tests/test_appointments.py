from datetime import datetime, timedelta
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_event import AuditEvent

def test_database_initialization_and_seed(db_session):
    appointments = db_session.query(Appointment).all()
    assert len(appointments) == 3

    for appt in appointments:
        assert isinstance(appt.id, int)

    statuses = [a.status for a in appointments]
    assert AppointmentStatus.CONFIRMED in statuses
    assert AppointmentStatus.PENDING in statuses

    types = [a.appointment_type for a in appointments]
    assert "Behavioral Health Intake" in types
    assert "Medication Review" in types
    assert "Counseling Session" in types

    audit_count = db_session.query(AuditEvent).count()
    assert audit_count == 0

def test_get_patient_appointments(client):
    response = client.get("/api/appointments?role=patient&user_id=patient-001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for appt in data:
        assert isinstance(appt["id"], int)
        assert appt["patient_id"] == "patient-001"
        assert appt["patient_name"] == "Olivia Carter"

def test_get_provider_appointments(client):
    response = client.get("/api/appointments?role=provider&user_id=provider-001")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for appt in data:
        assert isinstance(appt["id"], int)
        assert appt["provider_id"] == "provider-001"
        assert appt["provider_name"] == "Dr. Ethan Brooks"

def test_get_appointments_unfiltered(client):
    response = client.get("/api/appointments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_create_appointment(client):
    payload = {
        "patient_id": "patient-001",
        "patient_name": "Olivia Carter",
        "patient_email": "olivia.carter@email.test",
        "provider_id": "provider-001",
        "provider_name": "Dr. Ethan Brooks",
        "appointment_type": "Follow-up Visit",
        "reason": "Routine check",
        "requested_start": "2026-09-09T14:30:00Z"
    }
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["version"] == 1
    assert data["scheduled_start"].startswith("2026-09-09T14:30:00")
    assert data["scheduled_end"].startswith("2026-09-09T15:00:00")

def test_confirm_pending_appointment(client):
    # Appt 2 is pending in seed data
    response = client.post("/api/appointments/2/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"

def test_reject_confirming_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data
    response = client.post("/api/appointments/1/confirm")
    assert response.status_code == 400
    assert response.json()["detail"] == "Only pending appointments can be confirmed."

def test_cancel_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data
    response = client.post("/api/appointments/1/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"

def test_reject_cancelling_pending_appointment(client):
    # Appt 2 is pending in seed data
    response = client.post("/api/appointments/2/cancel")
    assert response.status_code == 400
    assert response.json()["detail"] == "Only confirmed appointments can be cancelled."

def test_reschedule_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data
    payload = {"scheduled_start": "2026-09-10T16:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["scheduled_start"].startswith("2026-09-10T16:00:00")
    assert data["scheduled_end"].startswith("2026-09-10T16:30:00")

def test_reschedule_pending_appointment(client):
    # Appt 2 is pending in seed data
    payload = {"scheduled_start": "2026-09-11T09:00:00Z"}
    response = client.post("/api/appointments/2/reschedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["scheduled_start"].startswith("2026-09-11T09:00:00")
    assert data["scheduled_end"].startswith("2026-09-11T09:30:00")

def test_verify_version_starts_at_1_on_creation(client):
    payload = {
        "patient_id": "patient-001",
        "patient_name": "Olivia Carter",
        "patient_email": "olivia.carter@email.test",
        "provider_id": "provider-001",
        "provider_name": "Dr. Ethan Brooks",
        "appointment_type": "Consultation",
        "requested_start": "2026-09-15T10:00:00Z"
    }
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 201
    assert response.json()["version"] == 1

def test_verify_scheduled_end_duration(client):
    payload = {
        "patient_id": "patient-001",
        "patient_name": "Olivia Carter",
        "patient_email": "olivia.carter@email.test",
        "provider_id": "provider-001",
        "provider_name": "Dr. Ethan Brooks",
        "appointment_type": "Consultation",
        "requested_start": "2026-09-20T08:15:00Z"
    }
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 201
    data = response.json()
    start = datetime.fromisoformat(data["scheduled_start"])
    end = datetime.fromisoformat(data["scheduled_end"])
    assert end - start == timedelta(minutes=30)
