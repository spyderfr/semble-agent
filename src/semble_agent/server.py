"""FastAPI server exposing the Semble agent as a REST API."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import Agent, AgentResult
from .config import load_config

app = FastAPI(
    title="Semble Agent API",
    description="REST API for the autonomous Semble browser agent.",
    version="0.1.0",
)

# In-memory task store (for async tasks)
_tasks: dict[str, dict[str, Any]] = {}


# --- Request / Response models ---


class TaskRequest(BaseModel):
    instruction: str
    provider: str | None = None


class TaskResponse(BaseModel):
    success: bool
    summary: str
    turns: int
    actions: list[dict[str, Any]]


class AsyncTaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: TaskResponse | None = None


class HealthResponse(BaseModel):
    status: str


# --- Endpoints ---


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/task", response_model=TaskResponse)
async def run_task(req: TaskRequest) -> TaskResponse:
    """Execute an instruction synchronously and return the result."""
    config = load_config()
    agent = Agent(config, provider=req.provider)
    try:
        result = await agent.run(req.instruction)
        return TaskResponse(
            success=result.success,
            summary=result.summary,
            turns=result.turns,
            actions=result.actions,
        )
    finally:
        await agent.close()


@app.post("/task/async", response_model=AsyncTaskResponse)
async def run_task_async(req: TaskRequest) -> AsyncTaskResponse:
    """Launch an instruction in the background and return a task ID."""
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "running", "result": None}

    asyncio.create_task(_run_background(task_id, req.instruction, req.provider))

    return AsyncTaskResponse(task_id=task_id, status="running")


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get the status and result of an async task."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    entry = _tasks[task_id]
    result = None
    if entry["result"] is not None:
        r: AgentResult = entry["result"]
        result = TaskResponse(
            success=r.success,
            summary=r.summary,
            turns=r.turns,
            actions=r.actions,
        )

    return TaskStatusResponse(
        task_id=task_id,
        status=entry["status"],
        result=result,
    )


async def _run_background(
    task_id: str, instruction: str, provider: str | None
) -> None:
    """Run an agent task in the background."""
    config = load_config()
    agent = Agent(config, provider=provider)
    try:
        result = await agent.run(instruction)
        _tasks[task_id] = {"status": "completed", "result": result}
    except Exception as exc:
        _tasks[task_id] = {
            "status": "failed",
            "result": AgentResult(
                success=False, summary=f"Internal error: {exc}", turns=0
            ),
        }
    finally:
        await agent.close()
