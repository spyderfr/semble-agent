# semble-agent

Autonomous agent that drives [Semble](https://app.semble.fr) via `agent-browser` using natural language instructions. Supports multiple LLM providers and exposes both a CLI and a REST API for orchestrator integration.

## Features

- **Multi-LLM support**: Anthropic (Claude), OpenAI (GPT-4), Cursor, Dust
- **REST API** (FastAPI): integrate with Workato, n8n, Make, Zapier, or any HTTP client
- **CLI**: run tasks directly from the terminal
- **Agent loop**: LLM decides → browser executes → LLM observes → repeat
- **Async tasks**: launch long-running tasks in the background and poll for results

## Project structure

```
src/semble_agent/
├── main.py          # CLI entry point (argparse)
├── server.py        # FastAPI REST API
├── agent.py         # Agent loop (LLM + browser)
├── browser.py       # agent-browser subprocess wrapper
├── prompts.py       # Semble-specific system prompts & tool definitions
├── config.py        # Configuration from .env
└── llm/
    ├── base.py      # Abstract LLMClient
    ├── anthropic.py # Claude client
    ├── openai.py    # GPT-4 client
    ├── cursor.py    # Cursor API client
    └── dust.py      # Dust API client
```

## Prerequisites

- Python 3.10+
- [agent-browser](https://www.npmjs.com/package/@anthropic/agent-browser) installed globally:
  ```bash
  npm install -g @anthropic/agent-browser
  ```

## Installation

```bash
git clone https://github.com/spyderfr/semble-agent.git
cd semble-agent
pip install -e ".[dev]"
```

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | Default provider: `claude`, `openai`, `cursor`, `dust` |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Claude) |
| `OPENAI_API_KEY` | OpenAI API key (for GPT-4) |
| `CURSOR_API_KEY` | Cursor API key |
| `DUST_API_KEY` | Dust API key |
| `DUST_WORKSPACE_ID` | Dust workspace ID |
| `SEMBLE_URL` | Semble app URL (default: `https://app.semble.fr`) |
| `SEMBLE_EMAIL` | Semble login email |
| `SEMBLE_PASSWORD` | Semble login password |
| `API_PORT` | REST API port (default: `8000`) |
| `API_HOST` | REST API host (default: `0.0.0.0`) |
| `MAX_TURNS` | Max agent loop iterations (default: `30`) |

## Usage

### CLI

```bash
# Run a task
python -m semble_agent "Crée un patient Bernard Tapie né le 25/10/1972"

# Use a specific provider
python -m semble_agent --provider openai "Liste les patients"

# Verbose output
python -m semble_agent -v "Ajoute une consultation"
```

### API server

```bash
# Start the server
python -m semble_agent serve
python -m semble_agent serve --port 9000
```

### API endpoints

**Health check**
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

**Run a task (synchronous)**
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Crée un patient Bernard Tapie né le 25/10/1972", "provider": "claude"}'
```

**Run a task (async)**
```bash
# Launch
curl -X POST http://localhost:8000/task/async \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Liste les patients", "provider": "claude"}'
# {"task_id": "...", "status": "running"}

# Poll for result
curl http://localhost:8000/task/{task_id}
# {"task_id": "...", "status": "completed", "result": {...}}
```

## Docker

```bash
docker build -t semble-agent .
docker run -p 8000:8000 --env-file .env semble-agent
```

## Testing

```bash
pytest -v
```

## License

MIT
