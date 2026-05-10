"""LLM provider clients and factory."""

from __future__ import annotations

from ..config import Config
from .base import LLMClient, LLMResponse, ToolCall

__all__ = ["LLMClient", "LLMResponse", "ToolCall", "get_client"]


def get_client(provider: str, config: Config) -> LLMClient:
    """Create an LLM client for the given provider name.

    Args:
        provider: One of "claude", "openai", "cursor", "dust".
        config: Application configuration with API keys.

    Returns:
        An initialized LLMClient instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = provider.lower()

    if provider == "claude":
        from .anthropic import AnthropicClient

        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the claude provider")
        return AnthropicClient(api_key=config.anthropic_api_key)

    if provider == "openai":
        from .openai import OpenAIClient

        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai provider")
        return OpenAIClient(api_key=config.openai_api_key)

    if provider == "cursor":
        from .cursor import CursorClient

        if not config.cursor_api_key:
            raise ValueError("CURSOR_API_KEY is required for the cursor provider")
        return CursorClient(api_key=config.cursor_api_key)

    if provider == "dust":
        from .dust import DustClient

        if not config.dust_api_key or not config.dust_workspace_id:
            raise ValueError(
                "DUST_API_KEY and DUST_WORKSPACE_ID are required for the dust provider"
            )
        return DustClient(
            api_key=config.dust_api_key, workspace_id=config.dust_workspace_id
        )

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        f"Supported: claude, openai, cursor, dust"
    )
