# Project Overview

This repository contains two distinct sub‑projects, each located in its own folder:

## 📧 **email**  
The **email** project provides tools for working with email messages.  
Key components include:

- **`email_reader.py`** – Reads and parses incoming emails.  
- **`email_sender.py`** – Sends emails via SMTP with optional attachments.  
- **`email_summarizer.py`** – Generates concise summaries of email content using LLMs.  
- **`config.py`** – Central configuration (SMTP settings, credentials, etc.).  
- **`main.py`** – Example entry point that ties the utilities together.  

The folder also contains a **`README.md`** with detailed usage instructions for the email utilities.

## 💻 **coding**  
The **coding** project is a small AI‑assisted coding assistant.  
Main modules:

- **`agent.py`** – Core agent logic that orchestrates LLM interactions.  
- **`llm.py`** – Wrapper around the language model API.  
- **`parser.py`** – Parses code snippets and extracts relevant information.  
- **`prompt.py`** – Templates for prompts sent to the LLM.  
- **`utils.py`** – Helper functions used across the project.  
- **`config.py`** – Configuration for model selection, API keys, etc.  
- **`main.py`** – CLI entry point to run the coding assistant.  

A dedicated **`README.md`** inside the `coding/` folder provides further details on setup and usage.

---

### How to get started

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

2. **Explore each sub‑project**  
   - For email utilities, read `email/README.md` and run `python email/main.py`.  
   - For the coding assistant, read `coding/readme.md` and run `python coding/main.py`.

Feel free to explore, modify, and extend the tools to fit your workflow.

---

*Repository root README generated automatically.*