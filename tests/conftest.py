"""Pytest configuration and fixtures for CR Intelligence Platform tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base


# Use SQLite for tests
TEST_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///test.db"
TEST_DATABASE_URL_SYNC = "sqlite:///test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_engine():
    engine = create_engine(TEST_DATABASE_URL_SYNC, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sync_session(sync_engine) -> Generator[Session, None, None]:
    SyncSession = sessionmaker(bind=sync_engine)
    session = SyncSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL_ASYNC, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    AsyncSessionFactory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with AsyncSessionFactory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_s3():
    """Mock S3/MinIO client."""
    mock = MagicMock()
    mock.upload_artifact.return_value = "test/artifact/path"
    mock.download_artifact.return_value = b"test content"
    return mock
