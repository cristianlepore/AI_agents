import json
from config import YOU_COLOR, ASSISTANT_COLOR, RESET_COLOR
from prompt import get_full_system_prompt
from parser import extract_tool_invocations
from llm import execute_llm_call
from tools.registry import TOOL_REGISTRY

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
