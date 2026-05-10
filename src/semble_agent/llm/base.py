"""Abstract base class for LLM clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = ""
    raw: Any = None


class LLMClient(ABC):
    """Abstract base class for LLM provider clients."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        system: str = "",
    ) -> LLMResponse:
        """Send a chat completion request to the LLM.

        Args:
            messages: Conversation history in provider-neutral format.
            tools: Tool definitions the LLM can call.
            system: System prompt.

        Returns:
            LLMResponse with content and/or tool calls.
        """
