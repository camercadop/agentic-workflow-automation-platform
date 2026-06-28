"""Main FastAPI application module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette import status

from src.api.errors import ErrorCode, ErrorDetail
from src.api.routes import executions, plugins

app = FastAPI(
    title="Agentic Workflow Automation Platform",
    description="Plugin-based workflow automation platform with DAG-based pipelines.",
    version="0.1.0",
)

app.include_router(plugins.router)
app.include_router(executions.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    detail = ErrorDetail(ErrorCode.RESOURCE_ALREADY_EXISTS, "Resource already exists")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail.to_dict()},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": {"code": "RESOURCE_NOT_FOUND", "message": str(exc)}},
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
