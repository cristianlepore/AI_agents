import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from config import groq_client, GROQ_MODEL


def _build_prompt(subject: str, body: str) -> str:
    return f"""
Riassumi questa email in modo conciso in una frase.
EMAIL:
Subject: {subject}
Body: {body[:1000]}
OUTPUT:
- Riassunto breve (1 frase)
- Eventuali azioni richieste (1 frase)
"""


def summarize_email(subject: str, body: str) -> str:
    """Riassume una singola email tramite Groq LLM."""
    prompt = _build_prompt(subject, body)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content


def summarize_emails(emails: list[dict]) -> list[str]:
    """
    Riassume una lista di email.
    Ogni elemento deve avere le chiavi 'subject' e 'body'.
    Restituisce una lista di stringhe con i riassunti.
    """
    if not emails:
        return ["Nessuna nuova email da analizzare."]
    return [summarize_email(e["subject"], e["body"]) for e in emails]
