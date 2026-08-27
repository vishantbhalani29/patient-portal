import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_confirmation_notification(appointment_id: int, patient_name: str, patient_email: str) -> None:
        """
        Simulates sending a confirmation notification (email/SMS) to the patient.
        """
        msg = f"Would send appointment confirmation email to {patient_email} for appointment #{appointment_id}"
        logger.info(msg)
        print(msg)

    @staticmethod
    def safe_send_confirmation_notification(appointment_id: int, patient_name: str, patient_email: str) -> None:
        """
        Safe wrapper for BackgroundTasks that isolates any notification exception
        from affecting the HTTP response or database state.
        """
        try:
            NotificationService.send_confirmation_notification(
                appointment_id=appointment_id,
                patient_name=patient_name,
                patient_email=patient_email,
            )
        except Exception as e:
            logger.error(f"Notification background task failed for appointment #{appointment_id}: {e}")
