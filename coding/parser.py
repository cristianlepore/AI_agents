import json
from typing import Any, Dict, List, Tuple

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
