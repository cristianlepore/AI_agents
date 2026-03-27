import sys
from email_reader import read_emails
from email_summarizer import summarize_emails
from mcp_tools import mcp


def run_cli():
    """Modalità CLI: legge e stampa i riassunti delle email non lette."""
    emails = read_emails(limit=10, provider="both")
    if not emails:
        print("Nessuna email non letta.")
        return
    summaries = summarize_emails(emails)
    for e, s in zip(emails, summaries):
        print("-----")
        print(f"Oggetto: {e['subject']}")
        print(s)


def run_server():
    """Modalità MCP server: rimane in ascolto di tool call."""
    mcp.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        run_server()
    else:
        run_cli()
