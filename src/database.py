"""Database engine and session management."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
