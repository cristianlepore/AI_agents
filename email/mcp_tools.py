import json
from mcp.server.fastmcp import FastMCP
from email_reader import read_emails
from email_summarizer import summarize_emails
from email_sender import send_email

mcp = FastMCP("agent")


@mcp.tool()
def fetch_emails(limit: int = 10, provider: str = "both", mark_seen: bool = False) -> str:
    """Legge le ultime N email non lette dalla inbox del provider scelto."""
    try:
        emails = read_emails(limit, provider=provider, mark_seen=mark_seen)
        return json.dumps(emails, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool()
def fetch_and_summarize(limit: int = 10, provider: str = "both", mark_seen: bool = False) -> str:
    """Recupera le ultime N email non lette e le riassume in un unico passaggio."""
    try:
        emails = read_emails(limit, provider=provider, mark_seen=mark_seen)
        if not emails:
            return json.dumps([], ensure_ascii=False)
        summaries = summarize_emails(emails)
        result = [
            {"subject": e["subject"], "summary": s}
            for e, s in zip(emails, summaries)
        ]
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool()
def send_email_tool(to_address: str, subject: str, body: str, provider: str = "gmail", reply_to: str = None, in_reply_to: str = None) -> str:
    """Invia un'email usando il provider definito (gmail/murena)."""
    return send_email(
        to_address=to_address,
        subject=subject,
        body=body,
        provider=provider,
        reply_to=reply_to,
        in_reply_to=in_reply_to,
    )


@mcp.tool()
def reply_email_tool(original_message_id: str, to_address: str, subject: str, body: str, provider: str = "gmail") -> str:
    """Invia una risposta email impostando correttamente In-Reply-To/References."""
    return send_email(
        to_address=to_address,
        subject=subject,
        body=body,
        provider=provider,
        in_reply_to=original_message_id,
    )


@mcp.tool()
def summarize_email_list(emails_json: str) -> str:
    """Riassume una lista di email in formato JSON [{subject, body}]."""
    emails = json.loads(emails_json)
    summaries = summarize_emails(emails)
    return json.dumps(summaries, ensure_ascii=False)
