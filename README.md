# Agentic

Progetto di agent basato su LLM con strumenti (tool) per gestione file e email.

## Struttura del repository

- `coding/`: agente principale di coding e tool generici per file
- `email/`: modulo di gestione email (IMAP/SMTP), riassunto e invio attraverso strumenti MCP
- `.env`: variabili d'ambiente critiche (API key, credenziali email)
- `requirements.txt`: dipendenze Python

## 1) Setup

1. Crea virtualenv e attivalo

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

3. Configura variabili d'ambiente in `.env`:

- `GROQ_API_KEY` (Groq API key)
- `MAIL_SERVER`, `GMAIL_USERNAME`, `GMAIL_APP`, `MURENA_SERVER`, `MURENA_USERNAME`, `MURENA_APP`, `IMAP_PORT`

## 2) Uso modulo email

```bash
cd email
python3 main.py fetch --limit 5 --provider gmail --mark-seen
python3 main.py summarize --limit 5 --provider both --prepare-reply
python3 main.py summarize --limit 5 --provider both --prepare-reply --auto-send
python3 main.py reply --to destinatario@example.com --subject "Ciao" --body "Test" --provider gmail
```

## 3) Avvio server agent (MCP)

```bash
python3 email/main.py agent
```

## 4) Note

- `email/readme.md` contiene dettagli su variabili d'ambiente e comandi email.
- `coding/readme.md` descrive il modulo di coding agent.
- Per sicurezza, usa account di test e app password per SMTP/IMAP.
