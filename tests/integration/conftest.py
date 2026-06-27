"""Shared fixtures for API integration tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from src.api.main import app
from src.database import get_session

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def _setup_db() -> Generator[None, None, None]:
    SQLModel.metadata.create_all(_engine)
    yield
    SQLModel.metadata.drop_all(_engine)


def _override_session() -> Generator[Session, None, None]:
    with Session(_engine) as session:
        yield session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_session] = _override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
