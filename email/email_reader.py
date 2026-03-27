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


def read_emails(limit: int = 5, provider: str = "both") -> list[dict]:
    """
    Legge le ultime `limit` email non lette dalla inbox del provider.
    Restituisce una lista di dict con chiavi 'subject' e 'body'.
    """
    if provider == "gmail":
        mail = imaplib.IMAP4_SSL(MAIL_SERVER)
        mail.login(GMAIL_USERNAME, GMAIL_APP)
        mail.select("inbox")
        _, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:]
        emails_data = []
        for num in latest_ids:
            _, msg = mail.fetch(num, "(RFC822)")
            raw_message = msg[0][1]
            message = email.message_from_bytes(raw_message)
            subject = decode_mime_words(message["Subject"] or "")
            body = extract_text_from_email(message)
            emails_data.append({
                "subject": subject,
                "body": body[:2000]
            })
        mail.close()
        mail.logout()
        return emails_data
    elif provider == "murena":
        mail = imaplib.IMAP4_SSL(MURENA_SERVER, IMAP_PORT)
        mail.login(MURENA_USERNAME, MURENA_APP)
        mail.select("inbox")
        _, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:]
        emails_data = []
        for num in latest_ids:
            _, msg = mail.fetch(num, "(RFC822)")
            raw_message = msg[0][1]
            message = email.message_from_bytes(raw_message)
            subject = decode_mime_words(message["Subject"] or "")
            body = extract_text_from_email(message)
            emails_data.append({
                "subject": subject,
                "body": body[:2000]
            })
        mail.close()
        mail.logout()
        return emails_data
    elif provider == "both":
        emails_gmail = read_emails(limit, provider="gmail")
        emails_murena = read_emails(limit, provider="murena")
        return emails_gmail + emails_murena
    else:
        raise ValueError("Invalid provider")
