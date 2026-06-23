"""Main FastAPI application module."""

from fastapi import FastAPI

app = FastAPI(
    title="Agentic Workflow Automation Platform",
    description="Plugin-based workflow automation platform with DAG-based pipelines.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
