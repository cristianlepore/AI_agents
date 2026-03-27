# Agentic Email Module

Il modulo `email` gestisce lettura, riassunto e invio/riposta delle email tramite provider IMAP/SMTP (Gmail, Murena).

## 1) Variabili d'ambiente richieste

- `MAIL_SERVER` (es. `imap.gmail.com`)
- `GMAIL_USERNAME` (es. `user@gmail.com`)
- `GMAIL_APP` (app password SMTP/IMAP)
- `MURENA_SERVER` (es. `imap.murena.com`)
- `MURENA_USERNAME` (es. user@murena.io)
- `MURENA_APP` (app password SMTP/IMAP)
- `IMAP_PORT` (es. `993`)
- `GROQ_API_KEY` (per il summarizer)

## 2) Avvio server agent

```bash
cd /home/devops/Projects/Agentic/email
python3 main.py agent
```

## 3) CLI

### 3.1 Leggi email non lette

```bash
python3 main.py fetch --limit 5 --provider gmail --mark-seen
```

### 3.2 Riassumi email non lette

```bash
python3 main.py summarize --limit 5 --provider both --mark-seen
```

### 3.3 Invia una nuova email

```bash
python3 main.py reply --to destinatario@example.com --subject "Ciao" --body "Test" --provider gmail
```

### 3.4 Risposta a un messaggio esistente

```bash
python3 main.py reply --to destinatario@example.com --subject "Re: Oggetto" --body "Risposta" --provider gmail --in-reply-to "<msgid@example.com>"
```

## 4) Funzionalità aggiunta

- `read_emails(limit, provider, mark_seen)` ora può segnare i messaggi come letti con `\Seen`.
- `send_email` valida gli indirizzi (pattern base) e fa logging in caso di errore.
- `mcp_tools` espone `send_email_tool` e `reply_email_tool`.

## 5) Note

- Per test locale, usa account di test e app password.
- Su Gmail, attiva IMAP e crea una app password se hai 2FA.
- `mark-seen` è opzionale, lascia le email non lette se non passato.

## 6) Preparazione risposta automatica su azione richiesta

- Usa `--prepare-reply` con `summarize` per generare bozza risposta quando l'email presenta azioni richieste.
- Usa `--auto-send` con attenzione per inviare direttamente la bozza creata (solo se confidi nella logica e nei destinatari):

```bash
python3 main.py summarize --limit 5 --provider both --prepare-reply
python3 main.py summarize --limit 5 --provider both --prepare-reply --auto-send
```

- La bozza viene generata con LLM Groq usando `generate_reply_draft` di `email_summarizer.py`. Sarà inviata con `send_email` a `from` dell'email originale e con `Re:` nell'oggetto.

## 7) Decisione "leggi → suggerisci → invia"

- Quando usi `python3 main.py summarize --prepare-reply`, il sistema:
  1. legge le email non lette
  2. genera riassunto e individua l'azione richiesta
  3. suggerisce bozza di risposta solo per email con azione presente

- Se passi `--auto-send`, invia automaticamente le risposte suggerite in un ciclo.
- Se non c’è alcuna azione, stampa: `Suggerimento: non è necessario rispondere`.


