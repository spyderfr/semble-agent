"""Cursor CLI/SDK LLM client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import LLMClient, LLMResponse, ToolCall


class CursorClient(LLMClient):
    """LLM client that proxies through Cursor's API.

    Cursor exposes an OpenAI-compatible endpoint, so this client sends
    requests to the Cursor API using the same chat completions format.
    """

    BASE_URL = "https://api.cursor.com/v1"

    def __init__(self, api_key: str, model: str = "cursor-small") -> None:
        self.api_key = api_key
        self.model = model
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert to OpenAI-compatible function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            }
            for t in tools
        ]

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str = "",
    ) -> LLMResponse:
        full_messages = list(messages)
        if system:
            full_messages.insert(0, {"role": "system", "content": system})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
        }
        if tools:
            payload["tools"] = self._convert_tools(tools)

        resp = await self._http.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        content = choice["message"].get("content", "") or ""

        tool_calls = []
        for tc in choice["message"].get("tool_calls") or []:
            tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                )
            )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=choice.get("finish_reason", ""),
            raw=data,
        )
