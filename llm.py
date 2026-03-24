from typing import List, Dict
from config import client

def execute_llm_call(conversation: List[Dict[str, str]]):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation,
        temperature=0.2
    )

    return response.choices[0].message.content
