import logging
import re
import smtplib
from email.message import EmailMessage
from config import MAIL_SERVER, GMAIL_USERNAME, GMAIL_APP, MURENA_SERVER, MURENA_USERNAME, MURENA_APP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _smtp_credentials(provider: str):
    if provider.lower() == "gmail":
        return MAIL_SERVER, 465, GMAIL_USERNAME, GMAIL_APP
    elif provider.lower() == "murena":
        return MURENA_SERVER, 465, MURENA_USERNAME, MURENA_APP
    else:
        raise ValueError("Provider non supportato. Usa 'gmail' o 'murena'.")


def _validate_email(address: str) -> None:
    if not address or not EMAIL_REGEX.match(address):
        raise ValueError(f"Indirizzo email non valido: {address}")


def send_email(to_address: str, subject: str, body: str, provider: str = "gmail", reply_to: str | None = None, in_reply_to: str | None = None) -> str:
    """Invia un email (o una risposta) tramite SMTP del provider selezionato."""
    _validate_email(to_address)
    if reply_to:
        _validate_email(reply_to)

    server, port, username, password = _smtp_credentials(provider)
    _validate_email(username)

    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = to_address
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(server, port, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(msg)
        logger.info("Email inviata a %s con subject %s via %s", to_address, subject, provider)
        return f"Email inviata a {to_address} con subject '{subject}'."
    except Exception as exc:
        logger.exception("Invio email fallito a %s via %s: %s", to_address, provider, exc)
        raise

