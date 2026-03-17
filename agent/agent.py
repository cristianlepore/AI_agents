import inspect
import json
import os

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ======================
# SETUP
# ======================

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

YOU_COLOR = "\u001b[94m"
ASSISTANT_COLOR = "\u001b[93m"
RESET_COLOR = "\u001b[0m"

# ======================
# UTILS
# ======================

def resolve_abs_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path

# ======================
# TOOLS
# ======================

def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file provided by the user.
    """
    full_path = resolve_abs_path(filename)

    with open(str(full_path), "r") as f:
        content = f.read()

    return {
        "file_path": str(full_path),
        "content": content
    }

def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists files in a directory.
    """
    full_path = resolve_abs_path(path)

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

def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replace old_str with new_str. If old_str is empty, create file.
    """
    full_path = resolve_abs_path(path)

    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}

    original = full_path.read_text(encoding="utf-8")

    if original.find(old_str) == -1:
        return {"path": str(full_path), "action": "old_str not found"}

    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")

    return {"path": str(full_path), "action": "edited"}

# ======================
# TOOL REGISTRY
# ======================

TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}

# ======================
# PROMPT
# ======================

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

def get_full_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += "\n===============\n"

    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)

# ======================
# PARSER
# ======================

def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    invocations = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line.startswith("tool:"):
            continue

        try:
            after = line[len("tool:"):].strip()
            name, rest = after.split("(", 1)

            if not rest.endswith(")"):
                continue

            args = json.loads(rest[:-1].strip())
            invocations.append((name.strip(), args))

        except Exception:
            continue

    return invocations

# ======================
# LLM CALL
# ======================

def execute_llm_call(conversation: List[Dict[str, str]]):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        temperature=0.2
    )

    return response.choices[0].message.content

# ======================
# AGENT LOOP
# ======================

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
