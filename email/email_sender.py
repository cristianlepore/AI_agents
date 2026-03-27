import logging
import re
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from config import MAIL_SERVER, GMAIL_USERNAME, GMAIL_APP, MURENA_SERVER, MURENA_USERNAME, MURENA_APP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(addr: str) -> str:
    """Estrae l'indirizzo da un formato name <email> o email puro."""
    if not addr or not addr.strip():
        raise ValueError(f"Indirizzo email non valido: {addr}")
    realname, email_addr = parseaddr(addr)
    email_addr = email_addr.strip()
    if not email_addr:
        raise ValueError(f"Indirizzo email non valido: {addr}")
    if not EMAIL_REGEX.match(email_addr):
        raise ValueError(f"Indirizzo email non valido: {addr}")
    return email_addr


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
    to_address = _normalize_email(to_address)
    if reply_to:
        reply_to = _normalize_email(reply_to)

    server, port, username, password = _smtp_credentials(provider)
    username = _normalize_email(username)

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

