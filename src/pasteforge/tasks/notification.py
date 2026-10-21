from pasteforge.exceptions import EmailDeliveryError
from pasteforge.infrastructure.email import EmailHandler
from pasteforge.infrastructure.worker import celery_app


@celery_app.task(autoretry_for=(EmailDeliveryError,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_notification_email(email: str, subject: str, content: str):
    EmailHandler().send_email(email, subject, content)
