from datetime import datetime, timedelta
from unittest.mock import patch
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_event import AuditEvent
from app.services.notification_service import NotificationService

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
    assert audit_count >= 3  # Initial seed request events

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
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert response.status_code == 200
    assert response.json()["version"] == 2

def test_confirm_with_stale_version_returns_409(client):
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 99})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_cancel_with_stale_version_returns_409(client):
    response = client.post("/api/appointments/1/cancel", json={"expected_version": 99})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_reschedule_with_stale_version_returns_409(client):
    payload = {"expected_version": 99, "scheduled_start": "2026-09-10T16:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_APPOINTMENT"
    assert body["message"] == "This appointment was updated by another user."
    assert body["current_version"] == 1

def test_version_increments_after_confirm(client):
    res1 = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    res2 = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert res2.status_code == 409

def test_version_increments_after_cancel(client):
    res1 = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    res2 = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert res2.status_code == 409

def test_version_increments_after_reschedule(client):
    payload1 = {"expected_version": 1, "scheduled_start": "2026-09-10T16:00:00Z"}
    res1 = client.post("/api/appointments/1/reschedule", json=payload1)
    assert res1.status_code == 200
    assert res1.json()["version"] == 2
    payload2 = {"expected_version": 1, "scheduled_start": "2026-09-10T17:00:00Z"}
    res2 = client.post("/api/appointments/1/reschedule", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["current_version"] == 2

def test_appointment_remains_unchanged_after_409(client, db_session):
    original = db_session.query(Appointment).filter(Appointment.id == 1).first()
    orig_status = original.status
    orig_start = original.scheduled_start
    orig_version = original.version

    payload = {"expected_version": 999, "scheduled_start": "2026-09-25T12:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 409

    db_session.expire_all()
    unchanged = db_session.query(Appointment).filter(Appointment.id == 1).first()
    assert unchanged.status == orig_status
    assert unchanged.scheduled_start == orig_start
    assert unchanged.version == orig_version

# ==================================================
# PHASE 4 AUDIT HISTORY TESTS
# ==================================================

def test_create_appointment_creates_request_audit_event(client):
    payload = {
        "patient_id": "patient-001",
        "patient_name": "Olivia Carter",
        "patient_email": "olivia.carter@email.test",
        "provider_id": "provider-001",
        "provider_name": "Dr. Ethan Brooks",
        "appointment_type": "Diagnostic Check",
        "requested_start": "2026-09-22T09:00:00Z"
    }
    create_res = client.post("/api/appointments", json=payload)
    assert create_res.status_code == 201
    appt_id = create_res.json()["id"]

    history_res = client.get(f"/api/appointments/{appt_id}/history")
    assert history_res.status_code == 200
    events = history_res.json()
    assert len(events) == 1
    event = events[0]
    assert event["action"] == "request"
    assert event["actor_id"] == "patient-001"
    assert event["actor_role"] == "patient"
    assert event["before_state"] is None
    assert event["after_state"]["status"] == "pending"
    assert event["after_state"]["version"] == 1

def test_confirm_appointment_creates_confirm_audit_event(client):
    confirm_res = client.post(
        "/api/appointments/2/confirm",
        json={"expected_version": 1, "actor_id": "provider-001", "actor_role": "provider"}
    )
    assert confirm_res.status_code == 200

    history_res = client.get("/api/appointments/2/history")
    assert history_res.status_code == 200
    events = history_res.json()
    confirm_event = events[-1]
    assert confirm_event["action"] == "confirm"
    assert confirm_event["actor_id"] == "provider-001"
    assert confirm_event["actor_role"] == "provider"
    assert confirm_event["before_state"]["status"] == "pending"
    assert confirm_event["after_state"]["status"] == "confirmed"
    assert confirm_event["after_state"]["version"] == 2

def test_reschedule_appointment_creates_reschedule_audit_event(client):
    payload = {
        "expected_version": 1,
        "scheduled_start": "2026-09-10T16:00:00Z",
        "actor_id": "provider-001",
        "actor_role": "provider"
    }
    resched_res = client.post("/api/appointments/1/reschedule", json=payload)
    assert resched_res.status_code == 200

    history_res = client.get("/api/appointments/1/history")
    assert history_res.status_code == 200
    events = history_res.json()
    resched_event = events[-1]
    assert resched_event["action"] == "reschedule"
    assert resched_event["actor_id"] == "provider-001"
    assert resched_event["actor_role"] == "provider"
    assert resched_event["before_state"]["scheduled_start"].startswith("2026-09-01T10:00:00")
    assert resched_event["after_state"]["scheduled_start"].startswith("2026-09-10T16:00:00")
    assert resched_event["after_state"]["version"] == 2

def test_cancel_appointment_creates_cancel_audit_event(client):
    cancel_res = client.post(
        "/api/appointments/1/cancel",
        json={"expected_version": 1, "actor_id": "patient-001", "actor_role": "patient"}
    )
    assert cancel_res.status_code == 200

    history_res = client.get("/api/appointments/1/history")
    assert history_res.status_code == 200
    events = history_res.json()
    cancel_event = events[-1]
    assert cancel_event["action"] == "cancel"
    assert cancel_event["actor_id"] == "patient-001"
    assert cancel_event["actor_role"] == "patient"
    assert cancel_event["before_state"]["status"] == "confirmed"
    assert cancel_event["after_state"]["status"] == "cancelled"

def test_audit_events_chronological_order(client):
    c1 = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert c1.status_code == 200
    r1 = client.post("/api/appointments/2/reschedule", json={"expected_version": 2, "scheduled_start": "2026-09-15T14:00:00Z"})
    assert r1.status_code == 200
    x1 = client.post("/api/appointments/2/cancel", json={"expected_version": 3})
    assert x1.status_code == 200

    history = client.get("/api/appointments/2/history").json()
    actions = [e["action"] for e in history]
    assert actions == ["request", "confirm", "reschedule", "cancel"]

def test_failed_stale_version_mutation_creates_no_audit_event(client):
    initial_history = client.get("/api/appointments/1/history").json()
    initial_count = len(initial_history)

    stale_res = client.post("/api/appointments/1/confirm", json={"expected_version": 999})
    assert stale_res.status_code == 409

    after_history = client.get("/api/appointments/1/history").json()
    assert len(after_history) == initial_count

def test_failed_business_rule_mutation_creates_no_audit_event(client):
    initial_history = client.get("/api/appointments/2/history").json()
    initial_count = len(initial_history)

    invalid_res = client.post("/api/appointments/2/cancel", json={"expected_version": 1})
    assert invalid_res.status_code == 400

    after_history = client.get("/api/appointments/2/history").json()
    assert len(after_history) == initial_count

def test_history_endpoint_returns_404_for_non_existent_appointment(client):
    response = client.get("/api/appointments/99999/history")
    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment not found"

# ==================================================
# PHASE 5 ASYNCHRONOUS NOTIFICATION TESTS
# ==================================================

@patch.object(NotificationService, "send_confirmation_notification")
def test_confirm_endpoint_schedules_notification(mock_notify, client):
    # Appt 2 is pending
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert response.status_code == 200
    assert mock_notify.called
    mock_notify.assert_called_once_with(
        appointment_id=2,
        patient_name="Olivia Carter",
        patient_email="olivia.carter@email.test"
    )

@patch.object(NotificationService, "send_confirmation_notification", side_effect=Exception("Email delivery service timeout"))
def test_appointment_confirmed_even_if_notification_raises_exception(mock_notify, client, db_session):
    # Appt 2 is pending
    response = client.post("/api/appointments/2/confirm", json={"expected_version": 1})
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Verify DB appointment state is successfully confirmed
    db_session.expire_all()
    appt = db_session.query(Appointment).filter(Appointment.id == 2).first()
    assert appt.status == AppointmentStatus.CONFIRMED

@patch.object(NotificationService, "send_confirmation_notification")
def test_notification_not_triggered_for_cancel(mock_notify, client):
    # Appt 1 is confirmed
    response = client.post("/api/appointments/1/cancel", json={"expected_version": 1})
    assert response.status_code == 200
    assert not mock_notify.called

@patch.object(NotificationService, "send_confirmation_notification")
def test_notification_not_triggered_for_reschedule(mock_notify, client):
    payload = {"expected_version": 1, "scheduled_start": "2026-09-10T16:00:00Z"}
    response = client.post("/api/appointments/1/reschedule", json=payload)
    assert response.status_code == 200
    assert not mock_notify.called
