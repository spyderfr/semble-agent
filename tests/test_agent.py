"""Tests for the Agent class."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from semble_agent.agent import Agent, AgentResult
from semble_agent.config import Config
from semble_agent.llm.base import LLMResponse, ToolCall


@pytest.fixture
def config():
    return Config(
        llm_provider="claude",
        anthropic_api_key="test-key",
        semble_url="https://app.semble.fr",
        semble_email="test@example.com",
        semble_password="password123",
        max_turns=5,
    )


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    return llm


@pytest.fixture
def agent(config, mock_llm):
    with patch("semble_agent.agent.get_client", return_value=mock_llm):
        a = Agent(config)
    return a


@pytest.mark.asyncio
async def test_agent_completes_without_tools(agent, mock_llm):
    """Agent returns immediately when LLM responds with text only."""
    mock_llm.chat.return_value = LLMResponse(
        content="Task completed: patient created.",
        tool_calls=[],
        stop_reason="end_turn",
    )

    result = await agent.run("Crée un patient Test")

    assert result.success is True
    assert "patient created" in result.summary.lower()
    assert result.turns == 1


@pytest.mark.asyncio
async def test_agent_executes_tool_then_completes(agent, mock_llm):
    """Agent executes a tool call then finishes on the next turn."""
    # First call: LLM wants to open a URL
    mock_llm.chat.side_effect = [
        LLMResponse(
            content="",
            tool_calls=[
                ToolCall(id="tc1", name="browser_open", arguments={"url": "https://app.semble.fr"})
            ],
            stop_reason="tool_use",
        ),
        LLMResponse(
            content="Opened the Semble login page successfully.",
            tool_calls=[],
            stop_reason="end_turn",
        ),
    ]

    with patch.object(agent.browser, "open") as mock_open:
        mock_open.return_value = MagicMock(success=True, output="OK", error="")
        result = await agent.run("Ouvre Semble")

    assert result.success is True
    assert result.turns == 2
    assert len(result.actions) == 1
    assert result.actions[0]["tool"] == "browser_open"


@pytest.mark.asyncio
async def test_agent_max_turns_exceeded(agent, mock_llm):
    """Agent stops and reports failure when max turns are exhausted."""
    # Always return a tool call so the agent never finishes
    mock_llm.chat.return_value = LLMResponse(
        content="",
        tool_calls=[
            ToolCall(id="tc1", name="browser_snapshot", arguments={})
        ],
        stop_reason="tool_use",
    )

    with patch.object(agent.browser, "snapshot") as mock_snap:
        mock_snap.return_value = MagicMock(success=True, output="page content", error="")
        result = await agent.run("Boucle infinie")

    assert result.success is False
    assert result.turns == agent.max_turns
    assert "maximum" in result.summary.lower()


@pytest.mark.asyncio
async def test_agent_handles_tool_error(agent, mock_llm):
    """Agent handles browser tool errors gracefully."""
    mock_llm.chat.side_effect = [
        LLMResponse(
            content="",
            tool_calls=[
                ToolCall(id="tc1", name="browser_click", arguments={"selector": "999"})
            ],
            stop_reason="tool_use",
        ),
        LLMResponse(
            content="Element not found, task failed.",
            tool_calls=[],
            stop_reason="end_turn",
        ),
    ]

    with patch.object(agent.browser, "click") as mock_click:
        mock_click.return_value = MagicMock(
            success=False, output="", error="Element not found"
        )
        result = await agent.run("Click sur element inexistant")

    assert result.success is True  # Agent decided to stop cleanly
    assert len(result.actions) == 1
    assert "ERROR" in result.actions[0]["result"]
