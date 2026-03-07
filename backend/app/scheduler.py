"""Scheduler de synchronisation automatique des données."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)


async def scheduled_sync():
    """Tâche planifiée de synchronisation DGFiP."""
    from app.database import AsyncSessionLocal
    from app.services.sync import sync_commune_finances

    logger.info(f"Synchronisation automatique déclenchée pour {settings.commune_insee}")
    async with AsyncSessionLocal() as db:
        try:
            rapport = await sync_commune_finances(db, settings.commune_insee)
            logger.info(f"Sync automatique terminée: {rapport}")
        except Exception as e:
            logger.error(f"Erreur sync automatique: {e}")


def start_scheduler() -> AsyncIOScheduler:
    """Démarre le scheduler APScheduler."""
    scheduler = AsyncIOScheduler()

    # Parser le cron depuis la config
    cron_parts = settings.sync_cron.split()
    if len(cron_parts) == 5:
        minute, hour, day, month, day_of_week = cron_parts
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )
    else:
        # Défaut: chaque dimanche à 3h
        trigger = CronTrigger(hour=3, minute=0, day_of_week="sun")

    scheduler.add_job(
        scheduled_sync,
        trigger=trigger,
        id="dgfip_sync",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler configuré: {settings.sync_cron}")
    return scheduler
