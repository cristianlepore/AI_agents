import argparse
import sys
from email_reader import read_emails
from email_sender import send_email
from email_summarizer import summarize_emails, generate_reply_draft
from mcp_tools import mcp


def run_cli():
    """Modalità CLI con fetch, summarize e invio/riposta."""
    parser = argparse.ArgumentParser(description="Email agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=False)

    fetch_parser = subparsers.add_parser("fetch", help="Legge email non lette")
    fetch_parser.add_argument("--limit", type=int, default=10, help="Numero di email da leggere")
    fetch_parser.add_argument("--provider", choices=["gmail", "murena", "both"], default="both")
    fetch_parser.add_argument("--mark-seen", action="store_true", help="Segna email come lette")

    summarize_parser = subparsers.add_parser("summarize", help="Riassume le email non lette")
    summarize_parser.add_argument("--prepare-reply", action="store_true", help="Genera bozza di risposta quando c'è un'azione richiesta")
    summarize_parser.add_argument("--auto-send", action="store_true", help="(ATTENZIONE) Invia automaticamente le risposte generate")

    reply_parser = subparsers.add_parser("reply", help="Invia una risposta tramite SMTP")
    reply_parser.add_argument("--to", required=True, help="Destinatario")
    reply_parser.add_argument("--subject", required=True, help="Oggetto")
    reply_parser.add_argument("--body", required=True, help="Corpo del messaggio")
    reply_parser.add_argument("--provider", choices=["gmail", "murena"], default="gmail")
    reply_parser.add_argument("--in-reply-to", default=None, help="Message-ID originale")
    reply_parser.add_argument("--reply-to", default=None, help="Header Reply-To")

    args = parser.parse_args()

    if args.command in (None, "fetch", "summarize"):
        emails = read_emails(limit=getattr(args, "limit", 10), provider=getattr(args, "provider", "both"), mark_seen=getattr(args, "mark_seen", False))
        if not emails:
            print("Nessuna email non letta.")
            return

        if args.command == "fetch":
            for e in emails:
                print("-----")
                print(f"Provider: {e['provider'].upper()}")
                print(f"Da: {e.get('from', '')}")
                print(f"Oggetto: {e['subject']}")
                print(e['body'][:1000])
            return

        summaries = summarize_emails(emails)
        prepare = getattr(args, "prepare_reply", False)
        auto_send = getattr(args, "auto_send", False)

        for e, s in zip(emails, summaries):
            print("-----")
            print(f"Provider: {e['provider'].upper()}")
            print(f"Da: {e.get('from', '')}")
            print(f"Oggetto: {e['subject']}")
            print("Riassunto:", s)

            if not prepare:
                continue

            draft = generate_reply_draft(e["subject"], e["body"], s)
            if not draft:
                print("Suggerimento: non è necessario rispondere (nessuna azione individuata).")
                continue

            print("Suggerimento: è consigliato rispondere con questa bozza:")
            print(draft)

            if auto_send:
                try:
                    sent = send_email(
                        to_address=e.get("from", ""),
                        subject=f"Re: {e['subject']}",
                        body=draft,
                        provider=e["provider"].lower(),
                        in_reply_to=e.get("message_id", None),
                    )
                    print("Invio automatico effettuato:", sent)
                except Exception as exc:
                    print("Errore invio automatico:", exc)

    elif args.command == "reply":
        result = send_email(
            to_address=args.to,
            subject=args.subject,
            body=args.body,
            provider=args.provider,
            reply_to=args.reply_to,
            in_reply_to=args.in_reply_to,
        )
        print(result)


def run_server():
    """Modalità MCP server: rimane in ascolto di tool call."""
    mcp.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        run_server()
    else:
        run_cli()
