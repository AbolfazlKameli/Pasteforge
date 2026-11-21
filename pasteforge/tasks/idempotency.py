import asyncio
import logging

from pasteforge.db.celery_database import CelerySessionLocal
from pasteforge.infrastructure.worker import celery_app
from pasteforge.repositories import IdempotencyRepository

logger = logging.getLogger(__name__)


async def _delete_expired_records() -> None:
    async with CelerySessionLocal() as db:
        repository = IdempotencyRepository(db)
        try:
            deleted_expired = await repository.delete_expired()
            await db.commit()
            logger.info("Idempotency record cleanup completed. Expired: %s", deleted_expired)
        except Exception:
            await db.rollback()
            logger.exception("Idempotency record cleanup failed.")
            raise


@celery_app.task
def delete_expired_records() -> None:
    asyncio.run(_delete_expired_records())
