class StaleAppointmentException(Exception):
    """Raised when an appointment update payload contains a stale expected_version."""
    def __init__(self, current_version: int):
        self.current_version = current_version
