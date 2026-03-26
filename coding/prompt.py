import inspect
from tools.registry import TOOL_REGISTRY

SYSTEM_PROMPT = """
You are a coding assistant whose goal is to solve coding tasks.

You have access to tools:

{tool_list_repr}


IMPORTANT RULES:

- ONLY use tools with this exact format:
  tool: TOOL_NAME({{JSON_ARGS}})

- Use single-line JSON with double quotes.

- DO NOT output JSON like:
  {{"name": "...", "arguments": ...}}

- DO NOT use any function calling or tool calling format other than:
  tool: TOOL_NAME({{JSON_ARGS}})

- If you use any other format, it is incorrect.

- After tool_result(...), continue the task.

- If no tool is needed, respond normally.
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
