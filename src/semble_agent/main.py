"""CLI entry point for semble-agent."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="semble-agent",
        description="Autonomous agent that drives Semble via agent-browser.",
    )
    parser.add_argument(
        "instruction",
        nargs="?",
        help="Natural-language instruction to execute (e.g. 'Crée un patient ...').",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "openai", "cursor", "dust"],
        default=None,
        help="LLM provider to use (default: from .env LLM_PROVIDER).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for the API server (default: 8000).",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host for the API server (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging."
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Sub-command: serve
    if args.instruction and args.instruction.strip().lower() == "serve":
        _run_server(args)
        return

    if not args.instruction:
        parser.print_help()
        sys.exit(1)

    # Run the agent with the given instruction
    asyncio.run(_run_agent(args))


async def _run_agent(args: argparse.Namespace) -> None:
    from .agent import Agent
    from .config import load_config

    config = load_config()
    agent = Agent(config, provider=args.provider)

    try:
        result = agent.run(args.instruction)
        outcome = await result
        if outcome.success:
            print(f"\n✓ Success ({outcome.turns} turns)")
            print(outcome.summary)
        else:
            print(f"\n✗ Failed ({outcome.turns} turns)")
            print(outcome.summary)
            sys.exit(1)
    finally:
        await agent.close()


def _run_server(args: argparse.Namespace) -> None:
    import uvicorn

    from .config import load_config

    config = load_config()
    host = args.host or config.api_host
    port = args.port or config.api_port

    uvicorn.run(
        "semble_agent.server:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
