"""Configuration loading from environment variables and .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment."""

    llm_provider: str = "claude"

    # API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    cursor_api_key: str = ""
    dust_api_key: str = ""
    dust_workspace_id: str = ""

    # Semble
    semble_url: str = "https://app.semble.fr"
    semble_email: str = ""
    semble_password: str = ""

    # Server
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    max_turns: int = 30


def load_config() -> Config:
    """Load configuration from .env file and environment variables."""
    # Look for .env in the project root (two levels up from this file)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    return Config(
        llm_provider=os.getenv("LLM_PROVIDER", "claude"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        cursor_api_key=os.getenv("CURSOR_API_KEY", ""),
        dust_api_key=os.getenv("DUST_API_KEY", ""),
        dust_workspace_id=os.getenv("DUST_WORKSPACE_ID", ""),
        semble_url=os.getenv("SEMBLE_URL", "https://app.semble.fr"),
        semble_email=os.getenv("SEMBLE_EMAIL", ""),
        semble_password=os.getenv("SEMBLE_PASSWORD", ""),
        api_port=int(os.getenv("API_PORT", "8000")),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        max_turns=int(os.getenv("MAX_TURNS", "30")),
    )
