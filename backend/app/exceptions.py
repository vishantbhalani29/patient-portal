class StaleAppointmentException(Exception):
    """Raised when an appointment update payload contains a stale expected_version."""
    def __init__(self, current_version: int):
        self.current_version = current_version

class ProviderScheduleConflictException(Exception):
    """Raised when confirming or rescheduling an appointment conflicts with an existing confirmed slot."""
    pass
