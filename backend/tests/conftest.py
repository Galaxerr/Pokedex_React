"""Fixtures for PostgreSQL integration tests.

The integration suite intentionally requires an explicit disposable test database.
It never falls back to the application DATABASE_URL and never drops or truncates data.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

TEST_DATABASE_ENV = "POKEDEX_TEST_DATABASE_URL"
SAFE_DATABASE_NAME = re.compile(r"(?:^|[_-])(test|testing|integration)(?:$|[_-])", re.I)


def _test_database_url() -> str:
    value = os.environ.get(TEST_DATABASE_ENV)
    if not value:
        pytest.fail(
            f"{TEST_DATABASE_ENV} must point to a dedicated PostgreSQL 16 test database; "
            "the integration suite does not use DATABASE_URL or skip."
        )
    parsed = make_url(value)
    if parsed.drivername != "postgresql+asyncpg":
        pytest.fail(f"{TEST_DATABASE_ENV} must use postgresql+asyncpg")
    if not parsed.database or not SAFE_DATABASE_NAME.search(parsed.database):
        pytest.fail(
            f"{TEST_DATABASE_ENV} database name must explicitly contain test/testing/integration"
        )
    if parsed.host not in {"localhost", "127.0.0.1", "::1", "postgres"}:
        pytest.fail(f"{TEST_DATABASE_ENV} host is not an approved local test host")
    return value


@pytest_asyncio.fixture(scope="session")
async def migrated_test_database() -> AsyncIterator[AsyncEngine]:
    """Run Alembic only after proving the public schema is empty."""

    database_url = _test_database_url()
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            existing = await connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
                )
            )
            tables = sorted(row[0] for row in existing)
        if tables:
            pytest.fail(
                "Refusing integration tests because the dedicated database is not empty: "
                + ", ".join(tables)
            )

        backend_dir = Path(__file__).parents[1]
        env = os.environ.copy()
        env["DATABASE_URL"] = database_url
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend_dir,
            env=env,
            check=True,
        )
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def postgres_session(migrated_test_database: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Provide a real async session; tests explicitly commit persistence evidence."""

    session_factory = async_sessionmaker(migrated_test_database, expire_on_commit=False)
    async with session_factory() as session:
        yield session
