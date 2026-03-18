import inspect
import json
import os
# Per la rilevazione dell'encoding dei file, utile per il tool di lettura dei file che deve gestire file con encoding sconosciuti
import chardet

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ======================
# SETUP
# ======================

# Carica le variabili d'ambiente dal file .env, in particolare la chiave API per Groq.
load_dotenv()
# Inizializza il client Groq con la chiave API ottenuta dalle variabili d'ambiente.
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Definisce i colori ANSI per differenziare visivamente i messaggi dell'utente e dell'assistente.
YOU_COLOR = "\u001b[94m"
# Colore giallo
ASSISTANT_COLOR = "\u001b[93m"
# Colore di reset per tornare al colore predefinito dopo i messaggi colorati.
RESET_COLOR = "\u001b[0m"

# ======================
# UTILS
# ======================

# Risolve un percorso relativo in un percorso assoluto.
# Necessario per gestire percorsi forniti dall'utente in modo coerente,
# garantendo che tutti i percorsi usati dal tool siano assoluti.
# Se il percorso è già assoluto, viene restituito così com'è. Se è relativo, viene risolto rispetto alla directory di lavoro corrente.
def resolve_abs_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    # Se il percorso non è assoluto, risolvi rispetto alla directory di lavoro corrente.
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path

# ======================
# TOOLS
# ======================

# Legge il contenuto completo di un file indicato dall'utente.
# Serve come tool per permettere all'agente di accedere a file arbitrari
# richiesti durante l'esecuzione di un task.
def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file provided by the user.
    """
    full_path = resolve_abs_path(filename)

    if not full_path.is_file():
        return {"error": "File not found or is a directory"}

    try:
        # Legge il file in modalità binaria
        with open(full_path, "rb") as f:
            raw_data = f.read()

        # Rileva encoding
        detected = chardet.detect(raw_data)
        encoding = detected["encoding"]

        # Fallback se non rilevato
        if encoding is None:
            encoding = "utf-8"

        # Decodifica il contenuto del file usando l'encoding rilevato, sostituendo i caratteri non decodificabili con un placeholder
        content = raw_data.decode(encoding, errors="replace")

    except Exception as e:
        return {"error": str(e)}

    return {
        "file_path": str(full_path),
        "encoding_used": encoding,
        "content": content
    }

# Elenca i file presenti in una directory.
# Utilizzato dal tool registry per fornire all'agente la capacità di
# esplorare il filesystem e presentare al modello la struttura dei file.
def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists files in a directory.
    """
    full_path = resolve_abs_path(path)

    # Se il percorso non è una directory, restituisce un errore. 
    all_files = []
    for item in full_path.iterdir():
        all_files.append({
            "filename": item.name,
            "type": "file" if item.is_file() else "dir"
        })

    return {
        "path": str(full_path),
        "files": all_files
    }

# Modifica (o crea) un file sostituendo una stringa esistente con una nuova.
# Questo è il cuore del tool "edit_file" che permette all'agente di
# apportare modifiche puntuali ai file del progetto.
def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replace old_str with new_str. If old_str is empty, create file.
    """
    full_path = resolve_abs_path(path)

    # Se old_str è vuota, si assume che il file debba essere creato con il contenuto di new_str. Se il file esiste già, verrà sovrascritto.
    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}

    # Se il file non esiste, restituisce un errore. Se esiste, legge il contenuto, sostituisce la prima occorrenza di old_str con new_str e riscrive il file.
    original = full_path.read_text(encoding="utf-8")

    if original.find(old_str) == -1:
        return {"path": str(full_path), "action": "old_str not found"}

    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")

    return {"path": str(full_path), "action": "edited"}

# ======================
# TOOL REGISTRY
# ======================

# Registra i tool disponibili in un dizionario, associando il nome del tool alla funzione che lo implementa. Questo registro è utilizzato per costruire il prompt di sistema e per eseguire i tool quando vengono invocati dall'LLM.
TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}

# ======================
# PROMPT
# ======================

# Genera una rappresentazione testuale di un tool (nome, descrizione, firma).
# Utilizzata per costruire il prompt di sistema che informa il modello
# sui tool disponibili.
def get_tool_str_representation(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return f"""
Name: {tool_name}
Description: {tool.__doc__}
Signature: {inspect.signature(tool)}
"""

SYSTEM_PROMPT = """
You are a coding assistant whose goal is to solve coding tasks.

You have access to tools:

{tool_list_repr}

When you want to use a tool, reply EXACTLY like:
tool: TOOL_NAME({{JSON_ARGS}})

Use single-line JSON with double quotes.
After tool_result(...), continue.
If no tool needed, respond normally.
"""

# Costruisce il prompt di sistema completo includendo la descrizione
# di tutti i tool registrati. Questo prompt è inviato al modello LLM
# all'inizio della sessione per fornire il contesto necessario.
def get_full_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += "\n===============\n"

    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)

# ======================
# PARSER
# ======================

# Analizza la risposta dell'LLM per estrarre le invocazioni di tool.
# Permette al ciclo dell'agente di capire quali tool devono essere
# eseguiti in base all'output del modello.
# Supporta sia il formato corretto "tool: TOOL_NAME({JSON_ARGS})" che un formato alternativo JSON più flessibile.
def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    invocations = []

    # Analizza ogni riga della risposta per cercare invocazioni di tool. Se una riga inizia con "tool:", tenta di estrarre il nome del tool e i suoi argomenti.
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line.startswith("tool:"):
            continue

        try:
            content = line[len("tool:"):].strip()

            # CASO 1: formato corretto
            if "(" in content:
                name, rest = content.split("(", 1)
                if rest.endswith(")"):
                    args = json.loads(rest[:-1].strip())
                    invocations.append((name.strip(), args))
                    continue

            # CASO 2: formato sbagliato tipo {"function_name": ..., "args": ...}
            parsed = json.loads(content)

            name = parsed.get("function_name")
            args_list = parsed.get("args", [])

            if name == "edit_file":
                args = {
                    "path": args_list[0],
                    "old_str": args_list[1],
                    "new_str": args_list[2]
                }
            elif name == "read_file":
                args = {"filename": args_list[0]}
            elif name == "list_files":
                args = {"path": args_list[0]}
            else:
                continue

            invocations.append((name, args))

        except Exception:
            continue

    return invocations

# ======================
# LLM CALL
# ======================

# Esegue una chiamata al modello LLM (Groq) con la conversazione corrente.
# Restituisce la risposta testuale del modello, che può contenere
# invocazioni di tool o messaggi di output.
def execute_llm_call(conversation: List[Dict[str, str]]):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation,
        temperature=0.2
    )

    return response.choices[0].message.content

# ======================
# AGENT LOOP
# ======================

# Avvia il loop principale dell'agente di coding.
# Gestisce l'interazione con l'utente, invoca l'LLM, interpreta le
# invocazioni di tool e aggiorna la conversazione finché l'utente
# non termina l'esecuzione.
def run_coding_agent_loop():
    print(get_full_system_prompt())

    conversation = [{
        "role": "system",
        "content": get_full_system_prompt()
    }]

    while True:
        try:
            user_input = input(f"{YOU_COLOR}You:{RESET_COLOR}:")
        except (KeyboardInterrupt, EOFError):
            break

        conversation.append({
            "role": "user",
            "content": user_input.strip()
        })

        while True:
            assistant_response = execute_llm_call(conversation)

            tool_invocations = extract_tool_invocations(assistant_response)

            if not tool_invocations:
                print(f"{ASSISTANT_COLOR}Assistant:{RESET_COLOR}: {assistant_response}")

                conversation.append({
                    "role": "assistant",
                    "content": assistant_response
                })
                break

            for name, args in tool_invocations:
                tool = TOOL_REGISTRY[name]

                if name == "read_file":
                    resp = tool(args.get("filename", "."))

                elif name == "list_files":
                    resp = tool(args.get("path", "."))

                elif name == "edit_file":
                    resp = tool(
                        args.get("path", "."),
                        args.get("old_str", ""),
                        args.get("new_str", "")
                    )

                conversation.append({
                    "role": "user",
                    "content": f"tool_result({json.dumps(resp)})"
                })

# ======================
# RUN
# ======================

if __name__ == "__main__":
    run_coding_agent_loop()
