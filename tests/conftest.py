"""Top-level test configuration.

Ensures DATABASE_URL is set to an in-memory SQLite database before
any application modules are imported. This prevents SQLAlchemy from
attempting to load database drivers (e.g., asyncpg) that may not be
installed in the test environment.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
