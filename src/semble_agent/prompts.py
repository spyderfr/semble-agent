"""System prompts for the Semble agent."""

SEMBLE_SYSTEM_PROMPT = """\
You are an autonomous agent that controls the Semble medical practice management \
application (app.semble.fr) through a browser. You receive natural-language \
instructions and execute them by interacting with the web application.

## Available tools

You can use the following browser tools:
- **browser_open(url)** – Navigate to a URL.
- **browser_snapshot()** – Get a text snapshot (accessibility tree) of the current page.
- **browser_click(selector)** – Click an element (use the ref number from the snapshot).
- **browser_fill(selector, value)** – Type text into an input field.
- **browser_select(selector, value)** – Select an option in a dropdown.
- **browser_scroll(direction)** – Scroll "up" or "down".
- **browser_wait(ms)** – Wait for a given number of milliseconds.
- **browser_go_back()** – Navigate back.
- **browser_screenshot()** – Take a screenshot of the current page.

## Semble application structure

- **Login page**: Email and password fields, then a "Se connecter" button.
- **Dashboard**: After login, the main dashboard with navigation sidebar.
- **Patients**: Sidebar → "Patients" → list of patients. Click "Nouveau patient" to create one.
- **Patient form**: Fields include Prénom, Nom, Date de naissance, Sexe, Email, Téléphone.
- **Consultations**: Inside a patient record, "Consultations" tab.
- **Constantes / Vitals**: Inside a consultation or patient record.

## Workflow

1. First, take a snapshot to understand the current page state.
2. If not logged in, navigate to the Semble URL and log in using the provided credentials.
3. Perform the requested task step by step.
4. After each action, take a snapshot to verify the result.
5. When done, report what was accomplished.

## Rules

- Always take a snapshot before and after important actions.
- Use ref numbers from the snapshot for click and fill operations.
- Wait briefly after page navigations for content to load.
- If an action fails, retry once before reporting failure.
- Be precise with form data – use exactly what was requested.
- Report success or failure clearly at the end.
"""

BROWSER_TOOLS = [
    {
        "name": "browser_open",
        "description": "Navigate to a URL in the browser.",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "The URL to navigate to."}},
            "required": ["url"],
        },
    },
    {
        "name": "browser_snapshot",
        "description": "Get a text snapshot (accessibility tree) of the current page.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_click",
        "description": "Click an element on the page by its ref number from the snapshot.",
        "parameters": {
            "type": "object",
            "properties": {"selector": {"type": "string", "description": "The ref number or selector to click."}},
            "required": ["selector"],
        },
    },
    {
        "name": "browser_fill",
        "description": "Fill a text input field with a value.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "The ref number or selector of the input field."},
                "value": {"type": "string", "description": "The text to type into the field."},
            },
            "required": ["selector", "value"],
        },
    },
    {
        "name": "browser_select",
        "description": "Select an option from a dropdown.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "The ref number or selector of the dropdown."},
                "value": {"type": "string", "description": "The value to select."},
            },
            "required": ["selector", "value"],
        },
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the page in a direction.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Direction to scroll.",
                },
            },
            "required": ["direction"],
        },
    },
    {
        "name": "browser_wait",
        "description": "Wait for a given number of milliseconds.",
        "parameters": {
            "type": "object",
            "properties": {
                "milliseconds": {"type": "integer", "description": "Number of milliseconds to wait."},
            },
            "required": ["milliseconds"],
        },
    },
    {
        "name": "browser_go_back",
        "description": "Navigate back in the browser history.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current page.",
        "parameters": {"type": "object", "properties": {}},
    },
]
