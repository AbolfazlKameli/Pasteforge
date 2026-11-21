import asyncio
import logging

from pasteforge.db.celery_database import CelerySessionLocal
from pasteforge.infrastructure.worker import celery_app
from pasteforge.repositories import PastesRepository

logger = logging.getLogger(__name__)


async def _delete_expired_pastes() -> None:
    async with CelerySessionLocal() as db:
        repository = PastesRepository(db)
        try:
            deleted_anonymous = await repository.delete_expired_anonymous()
            deleted_authenticated = await repository.delete_unmanageable()

            await db.commit()

            logger.info(
                "Paste cleanup completed. Anonymous: %s, Authenticated: %s", deleted_anonymous, deleted_authenticated
            )
        except Exception:
            await db.rollback()
            logger.exception("Paste cleanup failed.")
            raise


@celery_app.task
def delete_expired_pastes() -> None:
    asyncio.run(_delete_expired_pastes())
