"""Core agent loop: LLM decides, browser executes, repeat."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from .browser import Browser
from .config import Config
from .llm import LLMClient, get_client
from .prompts import BROWSER_TOOLS, SEMBLE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Outcome of an agent run."""

    success: bool
    summary: str
    actions: list[dict[str, Any]] = field(default_factory=list)
    turns: int = 0


class Agent:
    """Autonomous agent that drives Semble through an LLM and a browser."""

    def __init__(self, config: Config, provider: str | None = None) -> None:
        self.config = config
        self.provider = provider or config.llm_provider
        self.llm: LLMClient = get_client(self.provider, config)
        self.browser = Browser()
        self.max_turns = config.max_turns

    async def run(self, instruction: str) -> AgentResult:
        """Execute a natural-language instruction against Semble.

        Args:
            instruction: What the user wants done in Semble.

        Returns:
            AgentResult with success/failure and action log.
        """
        logger.info("Starting agent with instruction: %s", instruction)

        # Build the system prompt with credentials
        system = SEMBLE_SYSTEM_PROMPT
        system += f"\n\n## Credentials\n- URL: {self.config.semble_url}\n"
        system += f"- Email: {self.config.semble_email}\n"
        system += f"- Password: {self.config.semble_password}\n"

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": instruction},
        ]
        actions: list[dict[str, Any]] = []

        for turn in range(1, self.max_turns + 1):
            logger.info("Turn %d/%d", turn, self.max_turns)

            response = await self.llm.chat(
                messages=messages, tools=BROWSER_TOOLS, system=system
            )

            # If the LLM returns text without tool calls, we're done
            if not response.tool_calls:
                logger.info("Agent finished: %s", response.content)
                return AgentResult(
                    success=True,
                    summary=response.content,
                    actions=actions,
                    turns=turn,
                )

            # Process each tool call
            tool_results = []
            for tc in response.tool_calls:
                result = self._execute_tool(tc.name, tc.arguments)
                actions.append(
                    {"tool": tc.name, "args": tc.arguments, "result": result}
                )
                tool_results.append(
                    {"tool_call_id": tc.id, "name": tc.name, "result": result}
                )
                logger.info("Tool %s → %s", tc.name, result[:200])

            # Append assistant message and tool results to conversation
            # Build the assistant message based on provider format
            assistant_content = self._build_assistant_message(response)
            messages.append({"role": "assistant", "content": assistant_content})

            # Add tool results as user message (provider-neutral)
            tool_result_text = "\n".join(
                f"[{tr['name']}] {tr['result']}" for tr in tool_results
            )
            messages.append({"role": "user", "content": tool_result_text})

        # Exhausted turns
        logger.warning("Agent exhausted max turns (%d)", self.max_turns)
        return AgentResult(
            success=False,
            summary=f"Reached maximum number of turns ({self.max_turns}) without completing the task.",
            actions=actions,
            turns=self.max_turns,
        )

    def _build_assistant_message(self, response: Any) -> str:
        """Build a text representation of the assistant's response."""
        parts = []
        if response.content:
            parts.append(response.content)
        for tc in response.tool_calls:
            parts.append(f"[Calling {tc.name}({tc.arguments})]")
        return "\n".join(parts) if parts else "[tool calls]"

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """Execute a browser tool and return the result as a string."""
        try:
            if name == "browser_open":
                r = self.browser.open(args["url"])
            elif name == "browser_snapshot":
                r = self.browser.snapshot()
            elif name == "browser_click":
                r = self.browser.click(args["selector"])
            elif name == "browser_fill":
                r = self.browser.fill(args["selector"], args["value"])
            elif name == "browser_select":
                r = self.browser.select(args["selector"], args["value"])
            elif name == "browser_scroll":
                r = self.browser.scroll(args.get("direction", "down"))
            elif name == "browser_wait":
                r = self.browser.wait(args.get("milliseconds", 2000))
            elif name == "browser_go_back":
                r = self.browser.go_back()
            elif name == "browser_screenshot":
                r = self.browser.screenshot()
            else:
                return f"Unknown tool: {name}"

            if r.success:
                return r.output or "OK"
            return f"ERROR: {r.error}"
        except Exception as exc:
            logger.exception("Tool %s failed", name)
            return f"EXCEPTION: {exc}"

    async def close(self) -> None:
        """Clean up browser session."""
        self.browser.close()
