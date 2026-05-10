"""Wrapper around agent-browser subprocess commands."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


@dataclass
class BrowserResult:
    """Result of a browser command."""

    success: bool
    output: str
    error: str = ""


class Browser:
    """Drives a browser session via the agent-browser CLI."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self._session_id: str | None = None

    def _run(self, *args: str, timeout: int | None = None) -> BrowserResult:
        """Execute an agent-browser command and return the result."""
        cmd = ["agent-browser", *args]
        if self._session_id:
            cmd.extend(["--session", self._session_id])

        logger.debug("Running: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
            if proc.returncode != 0:
                logger.warning("agent-browser error: %s", proc.stderr)
                return BrowserResult(
                    success=False, output=proc.stdout, error=proc.stderr
                )
            return BrowserResult(success=True, output=proc.stdout)
        except subprocess.TimeoutExpired:
            logger.error("agent-browser timed out: %s", " ".join(cmd))
            return BrowserResult(success=False, output="", error="Command timed out")
        except FileNotFoundError:
            return BrowserResult(
                success=False,
                output="",
                error="agent-browser not found. Install it with: npm install -g @anthropic/agent-browser",
            )

    def open(self, url: str) -> BrowserResult:
        """Open a URL in the browser."""
        result = self._run("open", url)
        # Try to extract session id from output
        if result.success:
            try:
                data = json.loads(result.output)
                self._session_id = data.get("sessionId", self._session_id)
            except (json.JSONDecodeError, AttributeError):
                pass
        return result

    def snapshot(self) -> BrowserResult:
        """Get a text snapshot (accessibility tree) of the current page."""
        return self._run("snapshot")

    def click(self, selector: str) -> BrowserResult:
        """Click an element by selector or ref."""
        return self._run("click", selector)

    def fill(self, selector: str, value: str) -> BrowserResult:
        """Fill a text field with a value."""
        return self._run("fill", selector, value)

    def select(self, selector: str, value: str) -> BrowserResult:
        """Select an option from a dropdown."""
        return self._run("select", selector, value)

    def screenshot(self) -> BrowserResult:
        """Take a screenshot of the current page."""
        return self._run("screenshot")

    def scroll(self, direction: str = "down") -> BrowserResult:
        """Scroll the page up or down."""
        return self._run("scroll", direction)

    def wait(self, milliseconds: int = 2000) -> BrowserResult:
        """Wait for a specified duration."""
        return self._run("wait", str(milliseconds))

    def go_back(self) -> BrowserResult:
        """Navigate back in the browser history."""
        return self._run("go_back")

    def close(self) -> BrowserResult:
        """Close the browser session."""
        result = self._run("close")
        self._session_id = None
        return result
