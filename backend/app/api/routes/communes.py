"""Routes pour les communes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.commune import Commune
from app.schemas.commune import CommuneSchema, CommuneCreate
from app.services.dgfip import get_commune_info

router = APIRouter(prefix="/communes", tags=["Communes"])


@router.get("/{insee}", response_model=CommuneSchema)
async def get_commune(insee: str, db: AsyncSession = Depends(get_db)):
    """Récupère les informations d'une commune."""
    result = await db.execute(select(Commune).where(Commune.code_insee == insee))
    commune = result.scalar_one_or_none()

    if not commune:
        # Essayer de récupérer depuis l'API Geo
        info = await get_commune_info(insee)
        if not info:
            raise HTTPException(status_code=404, detail=f"Commune {insee} introuvable")

        commune = Commune(
            code_insee=insee,
            nom=info.get("nom", f"Commune {insee}"),
            population=info.get("population"),
            departement=info.get("departement"),
        )
        db.add(commune)
        await db.commit()
        await db.refresh(commune)

    return commune


@router.get("/", response_model=list[CommuneSchema])
async def list_communes(db: AsyncSession = Depends(get_db)):
    """Liste toutes les communes en base."""
    result = await db.execute(select(Commune).order_by(Commune.nom))
    return result.scalars().all()
