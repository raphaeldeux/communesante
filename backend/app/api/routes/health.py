"""Route de health check."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(tags=["Système"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Vérifie l'état de l'application et de la base de données."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "version": "1.0.0",
    }
