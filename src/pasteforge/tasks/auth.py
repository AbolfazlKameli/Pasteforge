from src.pasteforge.exceptions import EmailDeliveryError
from src.pasteforge.infrastructure.email import EmailHandler
from src.pasteforge.infrastructure.worker import celery_app


@celery_app.task(autoretry_for=(EmailDeliveryError,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_otp_code_email(email: str, otp_code: str):
    content = f"Your verification code is {otp_code}"
    subject = "Welcome to PasteForge"
    EmailHandler().send_email(email, subject, content)
