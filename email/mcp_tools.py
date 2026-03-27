import json
from mcp.server.fastmcp import FastMCP
from email_reader import read_emails
from email_summarizer import summarize_emails

mcp = FastMCP("agent")


@mcp.tool()
def fetch_emails(limit: int = 10) -> str:
    """Legge le ultime N email non lette dalla inbox Gmail."""
    emails = read_emails(limit)
    return json.dumps(emails, ensure_ascii=False)


@mcp.tool()
def fetch_and_summarize(limit: int = 10) -> str:
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
