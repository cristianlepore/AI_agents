import imaplib
import email
from email.header import decode_header
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def summarize_emails(emails):
    if not emails:
        return ["Nessuna nuova email da analizzare."]

    summaries = []

    for e in emails:
        prompt = f"""
Riassumi questa email in modo conciso in uan frase.

EMAIL:
Subject: {e['subject']}
Body: {e['body'][:1000]}

OUTPUT:
- Riassunto breve (1 frase)
- Eventuali azioni richieste (1 frase)
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        summaries.append(response.choices[0].message.content)

    return summaries

def decode_mime_words(s):
    decoded = decode_header(s)
    return "".join(
        str(t[0], t[1] or "utf-8") if isinstance(t[0], bytes) else t[0]
        for t in decoded
    )

def extract_text_from_email(message):
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

def read_emails(limit=5):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_APP")
    mail.login(username, password)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    # prendi solo le ultime N email
    latest_ids = email_ids[-limit:]

    emails_data = []

    for num in latest_ids:
        status, msg = mail.fetch(num, "(RFC822)")
        raw_message = msg[0][1]

        message = email.message_from_bytes(raw_message)

        subject = decode_mime_words(message["Subject"] or "")
        body = extract_text_from_email(message)

        emails_data.append({
            "subject": subject,
            "body": body[:2000]  # limita lunghezza
        })

    mail.close()
    mail.logout()

    return emails_data

def fetch_emails_tool(limit: int = 5):
    return read_emails(limit)

if __name__ == "__main__":
    emails = read_emails(5)
    summaries = summarize_emails(emails)

    for s in summaries:
        print("-----")
        print(s)
