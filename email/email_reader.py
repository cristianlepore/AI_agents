import imaplib
import email
from email.header import decode_header
from config import MAIL_SERVER, GMAIL_USERNAME, GMAIL_APP, MURENA_SERVER, MURENA_USERNAME, MURENA_APP, IMAP_PORT


def decode_mime_words(s: str) -> str:
    """Decodifica le parole MIME encoded in una stringa leggibile."""
    decoded = decode_header(s)
    return "".join(
        str(t[0], t[1] or "utf-8") if isinstance(t[0], bytes) else t[0]
        for t in decoded
    )


def extract_text_from_email(message) -> str:
    """Estrae il testo plain-text da un messaggio email (anche multipart)."""
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="replace")
    else:
        payload = message.get_payload(decode=True)
        if payload:
            return payload.decode(errors="replace")
    return ""


def _fetch_emails(mail, limit: int, mark_seen: bool, provider: str) -> list[dict]:
    _, messages = mail.search(None, "ALL")
    email_ids = messages[0].split() if messages and messages[0] else []
    latest_ids = email_ids[-limit:]

    emails_data = []
    for num in latest_ids:
        _, msg = mail.fetch(num, "(RFC822)")
        raw_message = msg[0][1]
        message = email.message_from_bytes(raw_message)

        emails_data.append({
            "subject": decode_mime_words(message.get("Subject", "") or ""),
            "body": extract_text_from_email(message)[:2000],
            "from": decode_mime_words(message.get("From", "") or ""),
            "message_id": message.get("Message-ID", ""),
            "provider": provider,
        })

        if mark_seen:
            mail.store(num, "+FLAGS", "\\Seen")

    return emails_data


def _open_mailbox(host: str, port: int | None, username: str, password: str):
    if port is None:
        return imaplib.IMAP4_SSL(host)
    return imaplib.IMAP4_SSL(host, port)


def _read_provider_emails(limit: int, provider: str, mark_seen: bool) -> list[dict]:
    if provider == "gmail":
        mail = _open_mailbox(MAIL_SERVER, None, GMAIL_USERNAME, GMAIL_APP)
        provider_name = "GMAIL"
        username, password = GMAIL_USERNAME, GMAIL_APP
    elif provider == "murena":
        mail = _open_mailbox(MURENA_SERVER, IMAP_PORT, MURENA_USERNAME, MURENA_APP)
        provider_name = "MURENA"
        username, password = MURENA_USERNAME, MURENA_APP
    else:
        raise ValueError("Invalid provider")

    mail.login(username, password)
    mail.select("inbox")
    try:
        return _fetch_emails(mail, limit, mark_seen, provider_name)
    finally:
        try:
            mail.close()
        except Exception:
            pass
        mail.logout()


def read_emails(limit: int = 5, provider: str = "both", mark_seen: bool = False) -> list[dict]:
    """
    Legge le ultime `limit` email non lette dalla inbox del provider.
    Restituisce una lista di dict con chiavi 'subject', 'body', 'provider'.
    """
    if provider == "both":
        return _read_provider_emails(limit, "gmail", mark_seen) + _read_provider_emails(limit, "murena", mark_seen)

    return _read_provider_emails(limit, provider, mark_seen)
