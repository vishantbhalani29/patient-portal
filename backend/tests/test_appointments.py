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
    # Appt 2 is pending in seed data, version = 1
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["version"] == 2

def test_reject_confirming_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data, version = 1
    response = client.post("/api/appointments/1/confirm", json={"expected_version": 1})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only pending appointments can be confirmed."

def test_cancel_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data, version = 1
    response = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["version"] == 2

def test_reject_cancelling_pending_appointment(client):
    # Appt 2 is pending in seed data, version = 1
    response = client.post("/api/appointments/2/cancel", json={"expected_version": 1})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only confirmed appointments can be cancelled."

def test_reschedule_confirmed_appointment(client):
    # Appt 1 is confirmed in seed data, version = 1
    payload = {"expected_version": 1, "scheduled_start": "2026-09-10T16:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["version"] == 2
    assert data["scheduled_start"].startswith("2026-09-10T16:00:00")
    assert data["scheduled_end"].startswith("2026-09-10T16:30:00")

def test_reschedule_pending_appointment(client):
    # Appt 2 is pending in seed data, version = 1
    payload = {"expected_version": 1, "scheduled_start": "2026-09-11T09:00:00Z"}
    response = client.post("/api/appointments/2/reschedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["version"] == 2
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

# ==================================================
# PHASE 3 OPTIMISTIC CONCURRENCY TESTS
# ==================================================

def test_confirm_with_correct_version(client):
    # Appt 2 is pending with version = 1
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert response.status_code == 200
    assert response.json()["version"] == 2

def test_confirm_with_stale_version_returns_409(client):
    # Appt 2 is pending with version = 1. Pass expected_version = 99
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 99})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_cancel_with_stale_version_returns_409(client):
    # Appt 1 is confirmed with version = 1. Pass expected_version = 99
    response = client.post("/api/appointments/1/cancel", json={"expected_version": 99})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_reschedule_with_stale_version_returns_409(client):
    # Appt 1 is confirmed with version = 1. Pass expected_version = 99
    payload = {"expected_version": 99, "scheduled_start": "2026-09-10T16:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_version_increments_after_confirm(client):
    # Appt 2 is pending with version = 1
    res1 = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    # Second confirm with stale version 1 now fails
    res2 = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert res2.status_code == 409

def test_version_increments_after_cancel(client):
    # Appt 1 is confirmed with version = 1
    res1 = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    # Second cancel with stale version 1 now fails
    res2 = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert res2.status_code == 409

def test_version_increments_after_reschedule(client):
    # Appt 1 is confirmed with version = 1
    payload1 = {"expected_version": 1, "scheduled_start": "2026-09-10T16:00:00Z"}
    res1 = client.post("/api/appointments/1/reschedule", json=payload1)
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    # Second reschedule with stale version 1 now fails
    payload2 = {"expected_version": 1, "scheduled_start": "2026-09-10T17:00:00Z"}
    res2 = client.post("/api/appointments/1/reschedule", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["current_version"] == 2

def test_appointment_remains_unchanged_after_409(client, db_session):
    # Appt 1 initial state
    original = db_session.query(Appointment).filter(Appointment.id == 1).first()
    orig_status = original.status
    orig_start = original.scheduled_start
    orig_version = original.version

    # Attempt mutation with stale version
    payload = {"expected_version": 999, "scheduled_start": "2026-09-25T12:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 409

    # Re-query DB and verify no changes occurred
    db_session.expire_all()
    unchanged = db_session.query(Appointment).filter(Appointment.id == 1).first()
    assert unchanged.status == orig_status
    assert unchanged.scheduled_start == orig_start
    assert unchanged.version == orig_version
