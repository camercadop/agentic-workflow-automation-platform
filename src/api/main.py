"""Main FastAPI application module."""

from fastapi import FastAPI

from src.api.routes import executions, plugins

app = FastAPI(
    title="Agentic Workflow Automation Platform",
    description="Plugin-based workflow automation platform with DAG-based pipelines.",
    version="0.1.0",
)

app.include_router(plugins.router)
app.include_router(executions.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
