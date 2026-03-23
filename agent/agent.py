import inspect
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Callable

from groq import Groq
from dotenv import load_dotenv

# ======================
# SETUP
# ======================

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

COLORS = {
    "user": "\u001b[94m",
    "assistant": "\u001b[93m",
    "reset": "\u001b[0m",
}

# ======================
# UTILS
# ======================

def resolve_abs_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    return path if path.is_absolute() else (Path.cwd() / path).resolve()

# ======================
# TOOLS
# ======================

def read_file_tool(filename: str) -> Dict[str, Any]:
    """Return full content of a file."""
    path = resolve_abs_path(filename)
    return {"file_path": str(path), "content": path.read_text(encoding="utf-8")}


def list_files_tool(path: str) -> Dict[str, Any]:
    """List files in a directory."""
    full_path = resolve_abs_path(path)

    files = [
        {"filename": item.name, "type": "file" if item.is_file() else "dir"}
        for item in full_path.iterdir()
    ]

    return {"path": str(full_path), "files": files}


def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """Replace old_str with new_str or create file if old_str is empty."""
    full_path = resolve_abs_path(path)

    if not old_str:
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}

    original = full_path.read_text(encoding="utf-8")

    if old_str not in original:
        return {"path": str(full_path), "action": "old_str_not_found"}

    full_path.write_text(original.replace(old_str, new_str, 1), encoding="utf-8")
    return {"path": str(full_path), "action": "edited"}

# ======================
# TOOL REGISTRY
# ======================

TOOL_REGISTRY: Dict[str, Callable] = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool,
}

# ======================
# PROMPT
# ======================

def get_tool_str(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return (
        f"Name: {tool_name}\n"
        f"Description: {tool.__doc__}\n"
        f"Signature: {inspect.signature(tool)}\n"
    )


def build_system_prompt() -> str:
    tools_repr = "\n===\n".join(get_tool_str(name) for name in TOOL_REGISTRY)

    return f"""
You are a coding assistant.

Tools:
{tools_repr}

Use tools like:
tool: TOOL_NAME({{JSON_ARGS}})
"""

# ======================
# PARSER
# ======================

def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    invocations = []

    for line in map(str.strip, text.splitlines()):
        if not line.startswith("tool:"):
            continue

        content = line[5:].strip()

        try:
            if "(" in content and content.endswith(")"):
                name, args_str = content.split("(", 1)
                args = json.loads(args_str[:-1])
                invocations.append((name.strip(), args))
                continue

            parsed = json.loads(content)
            name = parsed.get("function_name")
            args_list = parsed.get("args", [])

            mapping = {
                "edit_file": lambda a: {"path": a[0], "old_str": a[1], "new_str": a[2]},
                "read_file": lambda a: {"filename": a[0]},
                "list_files": lambda a: {"path": a[0]},
            }

            if name in mapping:
                invocations.append((name, mapping[name](args_list)))

        except Exception:
            continue

    return invocations

# ======================
# LLM CALL
# ======================

def execute_llm(conversation: List[Dict[str, str]]) -> str:
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        temperature=0.2,
    ).choices[0].message.content

# ======================
# TOOL EXECUTION
# ======================

def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        return {"error": f"Tool {name} not found"}

    try:
        return tool(**args)
    except Exception as e:
        return {"error": str(e)}

# ======================
# AGENT LOOP
# ======================

def run_agent():
    system_prompt = build_system_prompt()
    print(system_prompt)

    conversation = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input(f"{COLORS['user']}You:{COLORS['reset']} ")
        except (KeyboardInterrupt, EOFError):
            break

        conversation.append({"role": "user", "content": user_input.strip()})

        while True:
            response = execute_llm(conversation)
            tool_calls = extract_tool_invocations(response)

            if not tool_calls:
                print(f"{COLORS['assistant']}Assistant:{COLORS['reset']} {response}")
                conversation.append({"role": "assistant", "content": response})
                break

            for name, args in tool_calls:
                result = execute_tool(name, args)
                conversation.append({
                    "role": "user",
                    "content": f"tool_result({json.dumps(result)})"
                })

# ======================
# RUN
# ======================

if __name__ == "__main__":
    run_agent()