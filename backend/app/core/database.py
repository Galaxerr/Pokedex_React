"""Async SQLAlchemy engine, session factory, and declarative model registry."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all persisted domain models."""


engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one transaction-ready async session for an application request."""

    async with async_session_factory() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose pooled connections during application shutdown/tests."""

    await engine.dispose()
