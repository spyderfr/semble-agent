"""Tests for the Browser wrapper."""

from unittest.mock import MagicMock, patch

from semble_agent.browser import Browser, BrowserResult


def test_browser_open_success():
    browser = Browser()
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = '{"sessionId": "abc123"}'
    fake_proc.stderr = ""

    with patch("subprocess.run", return_value=fake_proc) as mock_run:
        result = browser.open("https://app.semble.fr")

    assert result.success is True
    assert "abc123" in result.output
    mock_run.assert_called_once()


def test_browser_open_failure():
    browser = Browser()
    fake_proc = MagicMock()
    fake_proc.returncode = 1
    fake_proc.stdout = ""
    fake_proc.stderr = "Connection refused"

    with patch("subprocess.run", return_value=fake_proc):
        result = browser.open("https://app.semble.fr")

    assert result.success is False
    assert result.error == "Connection refused"


def test_browser_snapshot():
    browser = Browser()
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "[1] button 'Login'\n[2] input 'Email'"
    fake_proc.stderr = ""

    with patch("subprocess.run", return_value=fake_proc):
        result = browser.snapshot()

    assert result.success is True
    assert "Login" in result.output


def test_browser_click():
    browser = Browser()
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "Clicked element"
    fake_proc.stderr = ""

    with patch("subprocess.run", return_value=fake_proc):
        result = browser.click("1")

    assert result.success is True


def test_browser_fill():
    browser = Browser()
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = "Filled"
    fake_proc.stderr = ""

    with patch("subprocess.run", return_value=fake_proc):
        result = browser.fill("2", "test@example.com")

    assert result.success is True


def test_browser_timeout():
    browser = Browser(timeout=1)
    import subprocess

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
        result = browser.open("https://app.semble.fr")

    assert result.success is False
    assert "timed out" in result.error.lower()


def test_browser_not_found():
    browser = Browser()

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        result = browser.open("https://app.semble.fr")

    assert result.success is False
    assert "not found" in result.error.lower()


def test_browser_close_resets_session():
    browser = Browser()
    browser._session_id = "abc123"
    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = ""
    fake_proc.stderr = ""

    with patch("subprocess.run", return_value=fake_proc):
        browser.close()

    assert browser._session_id is None
