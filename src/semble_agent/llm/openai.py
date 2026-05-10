"""OpenAI (GPT-4) LLM client."""

from __future__ import annotations

import json
from typing import Any

import openai

from .base import LLMClient, LLMResponse, ToolCall


class OpenAIClient(LLMClient):
    """LLM client using the OpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert generic tool definitions to OpenAI function-calling format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    },
                }
            )
        return openai_tools

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str = "",
    ) -> LLMResponse:
        # Prepend system message if provided
        full_messages = list(messages)
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
        }
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self._client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        content = choice.message.content or ""

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "",
            raw=response,
        )
