import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from config import groq_client, GROQ_MODEL


def _build_prompt(subject: str, body: str) -> str:
    return f"""
Riassumi questa email in modo conciso in circa 20 parole. Solo se lo ritieni necessario, puoi andare oltre le 20 parole per includere dettagli importanti.
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


def _build_reply_prompt(subject: str, body: str, action: str) -> str:
    return f"""
Stendi una bozza di risposta formale, chiara e breve in italiano all'email seguente.
Includi i punti essenziali per soddisfare l'azione richiesta.

EMAIL:
Subject: {subject}
Body: {body[:1000]}
AZIONE:
{action}

RISPOSTA:
"""


def _extract_action(summary: str) -> str:
    """Estrae la sezione azione dal riassunto prodotto."""
    if not summary:
        return ""
    lower = summary.lower()
    if "nessuna" in lower and "azione" in lower:
        return ""

    # cerca il secondo bullet o frase dopo "eventuali azioni richieste"
    lines = [line.strip(" -") for line in summary.splitlines() if line.strip()]
    for line in lines:
        if "azione" in line.lower() or "richiesta" in line.lower():
            if "nessuna" in line.lower():
                return ""
            return line
    # fallback: se la summary lunga contiene parole chiave, lo usa
    if "contattare" in lower or "rispondere" in lower or "seguire" in lower:
        return summary
    return ""


def generate_reply_draft(subject: str, body: str, summary: str) -> str:
    """Genera una bozza risposta se è stata individuata un'azione richiesta."""
    action = _extract_action(summary)
    if not action:
        return ""

    prompt = _build_reply_prompt(subject, body, action)
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def summarize_emails(emails: list[dict]) -> list[str]:
    """
    Riassume una lista di email.
    Ogni elemento deve avere le chiavi 'subject' e 'body'.
    Restituisce una lista di stringhe con i riassunti.
    """
    if not emails:
        return ["Nessuna nuova email da analizzare."]
    return [summarize_email(e["subject"], e["body"]) for e in emails]
