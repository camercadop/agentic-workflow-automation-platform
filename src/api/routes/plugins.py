"""Plugin API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from src.api.errors import raise_not_found
from src.api.schemas import PluginCreate, PluginResponse, PluginUpdate
from src.database import get_session
from src.models.plugin import Plugin
from src.repositories.plugins import PluginRepository

router = APIRouter(prefix="/plugins", tags=["plugins"])


def _get_repo(session: Annotated[Session, Depends(get_session)]) -> PluginRepository:
    return PluginRepository(session)


RepoDep = Annotated[PluginRepository, Depends(_get_repo)]


@router.get("/", response_model=list[PluginResponse])
def list_plugins(repo: RepoDep) -> list[Plugin]:
    """List all registered plugins."""
    return repo.list()


@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: uuid.UUID, repo: RepoDep) -> Plugin:
    """Get a plugin by ID."""
    plugin = repo.get(plugin_id)
    if plugin is None:
        raise_not_found("Plugin not found")
    return plugin


@router.post("/", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
def create_plugin(body: PluginCreate, repo: RepoDep) -> Plugin:
    """Register a new plugin."""
    plugin = Plugin(
        name=body.name,
        version=body.version,
        plugin_type=body.plugin_type,
        manifest=body.manifest,
    )
    return repo.create(plugin)


@router.patch("/{plugin_id}", response_model=PluginResponse)
def update_plugin(plugin_id: uuid.UUID, body: PluginUpdate, repo: RepoDep) -> Plugin:
    """Update a plugin's lifecycle state."""
    plugin = repo.get(plugin_id)
    if plugin is None:
        raise_not_found("Plugin not found")
    plugin.lifecycle_state = body.lifecycle_state
    return repo.update(plugin)


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plugin(plugin_id: uuid.UUID, repo: RepoDep) -> None:
    """Delete a plugin by ID."""
    plugin = repo.get(plugin_id)
    if plugin is None:
        raise_not_found("Plugin not found")
    repo.delete(plugin_id)
