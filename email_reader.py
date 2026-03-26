import imaplib
import email
from email.header import decode_header
from groq import Groq
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import json

load_dotenv()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
mcp = FastMCP("gmail-agent")

# ── Logica esistente (invariata) ───────────────────────────────────────────────

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
    mail = imaplib.IMAP4_SSL(os.getenv("MAIL_SERVER"))
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_APP")
    mail.login(username, password)
    mail.select("inbox")
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()
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
            "body": body[:2000]
        })
    mail.close()
    mail.logout()
    return emails_data

def summarize_emails(emails):
    if not emails:
        return ["Nessuna nuova email da analizzare."]
    summaries = []
    for e in emails:
        prompt = f"""
Riassumi questa email in modo conciso in una frase.
EMAIL:
Subject: {e['subject']}
Body: {e['body'][:1000]}
OUTPUT:
- Riassunto breve (1 frase)
- Eventuali azioni richieste (1 frase)
"""
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        summaries.append(response.choices[0].message.content)
    return summaries

# ── Tool MCP ───────────────────────────────────────────────────────────────────

@mcp.tool()
def fetch_emails(limit: int = 5) -> str:
    """Legge le ultime N email non lette dalla inbox Gmail."""
    emails = read_emails(limit)
    return json.dumps(emails, ensure_ascii=False)

@mcp.tool()
def fetch_and_summarize(limit: int = 5) -> str:
    """Recupera le ultime N email non lette e le riassume in un unico passaggio."""
    emails = read_emails(limit)
    summaries = summarize_emails(emails)
    result = [
        {"subject": e["subject"], "summary": s}
        for e, s in zip(emails, summaries)
    ]
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def summarize_email_list(emails_json: str) -> str:
    """Riassume una lista di email in formato JSON [{subject, body}]."""
    emails = json.loads(emails_json)
    summaries = summarize_emails(emails)
    return json.dumps(summaries, ensure_ascii=False)

# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # modalità MCP — aspetta tool call
        mcp.run()
    else:
        # modalità CLI — esegue subito e stampa
        emails = read_emails(5)
        if not emails:
            print("Nessuna email non letta.")
        else:
            summaries = summarize_emails(emails)
            for e, s in zip(emails, summaries):
                print("-----")
                print(f"Oggetto: {e['subject']}")
                print(s)