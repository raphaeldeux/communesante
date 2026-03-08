"""Application FastAPI principale - CommuneSante."""
import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.api.routes import communes, finances, indicateurs, health

# Configuration des logs
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation et nettoyage de l'application."""
    # Créer les tables si elles n'existent pas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Base de données initialisée")

    # Synchronisation initiale si la commune par défaut n'a pas de données
    from app.database import AsyncSessionLocal
    from app.models.commune import Commune
    from app.models.finance import ExerciceFinancier
    from app.services.sync import sync_commune_finances
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Commune).where(Commune.code_insee == settings.commune_insee)
        )
        commune = result.scalar_one_or_none()
        has_data = False
        if commune:
            ex = await db.execute(
                select(ExerciceFinancier)
                .where(ExerciceFinancier.commune_id == commune.id)
                .limit(1)
            )
            has_data = ex.scalar_one_or_none() is not None

        if not has_data:
            logger.info(f"Synchronisation initiale automatique pour {settings.commune_insee}")
            try:
                rapport = await sync_commune_finances(db, settings.commune_insee)
                logger.info(f"Sync initiale terminée: {rapport}")
            except Exception as e:
                logger.warning(f"Sync initiale non bloquante échouée: {e}")

    # Démarrer le scheduler de synchronisation
    from app.scheduler import start_scheduler
    scheduler = start_scheduler()
    logger.info("Scheduler démarré")

    yield

    # Arrêt propre
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title="CommuneSante API",
    description="Tableau de bord de la santé financière communale - Module Finances",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(communes.router)
app.include_router(finances.router)
app.include_router(indicateurs.router)


@app.get("/")
async def root():
    return {
        "app": "CommuneSante",
        "version": "1.0.0",
        "docs": "/docs",
    }
