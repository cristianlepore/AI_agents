from typing import List, Dict
from config import client

def execute_llm_call(conversation: List[Dict[str, str]]):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        temperature=0.2,
        tool_choice="none"
    )

    return response.choices[0].message.content
