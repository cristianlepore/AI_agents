import inspect
import json
import os
# Used for file encoding detection, useful for the file-reading tool
# which must handle files with unknown encodings
import chardet

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ======================
# SETUP
# ======================

# Loads environment variables from the .env file, in particular the Groq API key.
load_dotenv()

# Initializes the Groq client using the API key from environment variables.
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ANSI colors to visually distinguish user and assistant messages itestten the terminal.
YOU_COLOR = "\u001b[94m"        # Blue
ASSISTANT_COLOR = "\u001b[93m"  # Yellow
RESET_COLOR = "\u001b[0m"       # Reset to default color

# ======================
# UTILS
# ======================

# Resolves a relative path into an absolute path.
# This ensures consistency when handling user-provided paths.
# If the path is already absolute, it is returned as-is.
# Otherwise, it is resolved relative to the current working directory.
def resolve_abs_path(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path

# ======================
# TOOLS
# ======================

# Reads the full content of a file provided by the user.
# Allows the agent to access arbitrary files during task execution.
def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file provided by the user.
    """
    full_path = resolve_abs_path(filename)

    if not full_path.is_file():
        return {"error": "File not found or is a directory"}

    try:
        # Read file in binary mode
        with open(full_path, "rb") as f:
            raw_data = f.read()

        # Detect encoding
        detected = chardet.detect(raw_data)
        encoding = detected["encoding"]

        # Fallback if detection fails
        if encoding is None:
            encoding = "utf-8"

        # Decode content using detected encoding
        # Replace undecodable characters
        content = raw_data.decode(encoding, errors="replace")

    except Exception as e:
        return {"error": str(e)}

    return {
        "file_path": str(full_path),
        "encoding_used": encoding,
        "content": content
    }

# Lists files in a directory.
# Allows the agent to explore the filesystem structure.
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

# Edits (or creates) a file by replacing a string with another.
# Core tool that enables precise file modifications.
def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replace old_str with new_str. If old_str is empty, create file.
    """
    full_path = resolve_abs_path(path)

    # If old_str is empty → create/overwrite file
    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {"path": str(full_path), "action": "created_file"}

    # Read file and replace first occurrence
    original = full_path.read_text(encoding="utf-8")

    if original.find(old_str) == -1:
        return {"path": str(full_path), "action": "old_str not found"}

    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")

    return {"path": str(full_path), "action": "edited"}

# ======================
# TOOL REGISTRY
# ======================

# Registers available tools in a dictionary mapping tool names to functions.
TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}

# ======================
# PROMPT
# ======================

# Generates a textual representation of a tool (name, description, signature).
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

# Builds the full system prompt including all tool descriptions.
def get_full_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += "\n===============\n"

    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)

# ======================
# PARSER
# ======================

# Parses LLM output to extract tool invocations.
# Supports both correct format and fallback JSON format.
def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    invocations = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line.startswith("tool:"):
            continue

        try:
            content = line[len("tool:"):].strip()

            # CASE 1: correct format
            if "(" in content:
                name, rest = content.split("(", 1)
                if rest.endswith(")"):
                    args = json.loads(rest[:-1].strip())
                    invocations.append((name.strip(), args))
                    continue

            # CASE 2: fallback JSON format
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

# Calls the LLM with the current conversation.
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

# Main loop of the coding agent.
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