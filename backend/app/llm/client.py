import json

import anthropic

from app.config import settings
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.tools import TOOL_SCHEMAS, execute_tool

_MODEL = "claude-sonnet-5"
_MAX_TOOL_ITERATIONS = 6

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def ask(session, user_message):
    messages = [{"role": "user", "content": user_message}]

    for _ in range(_MAX_TOOL_ITERATIONS):
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = execute_tool(session, block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
            )
        messages.append({"role": "user", "content": tool_results})

    return "I wasn't able to finish gathering your data in time — please try asking again."
