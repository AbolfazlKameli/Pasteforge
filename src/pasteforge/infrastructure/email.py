import ssl
from email.message import EmailMessage
from smtplib import SMTP, SMTPAuthenticationError, SMTPException

from src.pasteforge.core.config import configs
from src.pasteforge.exceptions import EmailDeliveryError


class EmailHandler:
    @staticmethod
    def _login(smtp: SMTP) -> None:
        smtp.login(user=configs.EMAIL_HOST_USERNAME, password=configs.EMAIL_HOST_PASSWORD)

    @staticmethod
    def _prepare_message(to: str, subject: str, body: str) -> EmailMessage:
        msg = EmailMessage()
        msg['From'] = configs.EMAIL_HOST_USERNAME
        msg['To'] = to
        msg['Subject'] = subject
        msg.set_content(body)
        return msg

    def send_email(self, to: str, subject: str, body: str) -> None:
        msg = self._prepare_message(to, subject, body)
        try:
            with SMTP(host=configs.EMAIL_HOSTNAME, port=configs.EMAIL_PORT, timeout=10) as smtp:
                if configs.EMAIL_USE_TLS:
                    context = ssl.create_default_context()
                    smtp.starttls(context=context)

                self._login(smtp)
                smtp.send_message(msg)

        except SMTPAuthenticationError as exc:
            raise EmailDeliveryError('Email authentication failed') from exc

        except (SMTPException, OSError) as exc:
            raise EmailDeliveryError('Unable to send email') from exc
