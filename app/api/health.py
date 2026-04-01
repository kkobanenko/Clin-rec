from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import async_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {"status": "ok" if db_ok else "degraded", "database": db_ok}
