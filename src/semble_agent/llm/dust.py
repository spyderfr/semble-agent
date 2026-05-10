"""Dust API LLM client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import LLMClient, LLMResponse, ToolCall


class DustClient(LLMClient):
    """LLM client using the Dust conversation API.

    Dust manages its own LLM routing internally.  We create a conversation,
    post the user message (with tool definitions via MCP-style config), and
    poll for the assistant reply.
    """

    BASE_URL = "https://dust.tt/api/v1"

    def __init__(
        self, api_key: str, workspace_id: str, agent_id: str = "dust"
    ) -> None:
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.agent_id = agent_id
        self._http = httpx.AsyncClient(
            base_url=f"{self.BASE_URL}/w/{workspace_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str = "",
    ) -> LLMResponse:
        # Build the user content from the last message
        last_msg = messages[-1] if messages else {"content": ""}
        user_content = last_msg.get("content", "")

        if system:
            user_content = f"{system}\n\n{user_content}"

        # Create a new conversation
        conv_resp = await self._http.post(
            "/assistant/conversations",
            json={"title": "semble-agent", "visibility": "unlisted"},
        )
        conv_resp.raise_for_status()
        conv_data = conv_resp.json()
        conv_id = conv_data["conversation"]["sId"]

        # Post a message
        msg_payload: dict[str, Any] = {
            "content": user_content,
            "context": {
                "timezone": "Europe/Paris",
                "profilePictureUrl": None,
                "fullName": "Semble Agent",
                "email": None,
                "origin": "api",
            },
            "mentions": [{"configurationId": self.agent_id}],
        }

        msg_resp = await self._http.post(
            f"/assistant/conversations/{conv_id}/messages",
            json=msg_payload,
        )
        msg_resp.raise_for_status()

        # Poll for agent reply
        import asyncio

        content = ""
        for _ in range(60):
            await asyncio.sleep(2)
            events_resp = await self._http.get(
                f"/assistant/conversations/{conv_id}/events",
            )
            events_resp.raise_for_status()
            events = events_resp.json().get("events", [])

            for event in events:
                if event.get("type") == "agent_message_success":
                    content = event.get("message", {}).get("content", "")
                    break
            if content:
                break

        # Dust handles tool execution internally, so we return plain text.
        # If the response contains structured tool-call JSON, parse it.
        tool_calls: list[ToolCall] = []
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                for tc in parsed["tool_calls"]:
                    tool_calls.append(
                        ToolCall(
                            id=tc.get("id", ""),
                            name=tc["name"],
                            arguments=tc.get("arguments", {}),
                        )
                    )
                content = parsed.get("content", "")
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason="end_turn",
            raw=None,
        )
