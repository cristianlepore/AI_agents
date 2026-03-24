import inspect
from tools.registry import TOOL_REGISTRY

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

def get_tool_str_representation(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return f"""
Name: {tool_name}
Description: {tool.__doc__.strip().replace('\n', ' ')}
Signature: {inspect.signature(tool)}
"""

def get_full_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += "\n===============\n"

    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)
