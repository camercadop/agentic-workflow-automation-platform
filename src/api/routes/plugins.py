"""Plugin API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas import PluginCreate, PluginResponse
from src.database import get_session
from src.models.plugin import Plugin
from src.repositories.plugins import PluginRepository

router = APIRouter(prefix="/plugins", tags=["plugins"])


def _get_repo(session: Annotated[Session, Depends(get_session)]) -> PluginRepository:
    return PluginRepository(session)


RepoDep = Annotated[PluginRepository, Depends(_get_repo)]


@router.get("/", response_model=list[PluginResponse])
def list_plugins(repo: RepoDep) -> list[Plugin]:
    return repo.list()


@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: uuid.UUID, repo: RepoDep) -> Plugin:
    plugin = repo.get(plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.post("/", response_model=PluginResponse, status_code=201)
def create_plugin(body: PluginCreate, repo: RepoDep) -> Plugin:
    plugin = Plugin(
        name=body.name,
        version=body.version,
        plugin_type=body.plugin_type,
        manifest=body.manifest,
    )
    return repo.create(plugin)
