from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def require_api_key(x_crin_api_key: str | None = Header(default=None)) -> None:
    """Protect non-health API routes when auth is enabled via env settings."""
    if not settings.api_auth_enabled:
        return
    configured = (settings.api_key or "").strip()
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API auth enabled but CRIN_API_KEY is not configured",
        )
    if x_crin_api_key != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
