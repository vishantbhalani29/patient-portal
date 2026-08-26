from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_event import AuditEvent

def test_database_initialization_and_seed(db_session):
    # Verify tables created and seeded
    appointments = db_session.query(Appointment).all()
    assert len(appointments) == 3

    for appt in appointments:
        assert isinstance(appt.id, int)

    statuses = [a.status for a in appointments]
    assert AppointmentStatus.CONFIRMED in statuses
    assert AppointmentStatus.PENDING in statuses

    # Verify original seed data names & types
    types = [a.appointment_type for a in appointments]
    assert "Behavioral Health Intake" in types
    assert "Medication Review" in types
    assert "Counseling Session" in types

    # Verify AuditEvent table structure exists
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
