"""Synchronous DB session for use in Celery workers."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True, pool_size=5, max_overflow=10)
SyncSessionFactory = sessionmaker(bind=sync_engine)


def get_sync_session() -> Session:
    return SyncSessionFactory()
