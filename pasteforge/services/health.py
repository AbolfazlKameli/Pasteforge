import asyncio
import uuid
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from pasteforge.dependencies import db_dependency, redis_dependency
from pasteforge.infrastructure.worker import celery_app


class HealthService:
    def __init__(self, db: db_dependency, redis: redis_dependency):
        self.db = db
        self.redis = redis

    async def check_health(self):
        postgres, redis, celery = await asyncio.gather(self.check_postgres(), self.check_redis(), self.check_celery())
        checks = {"postgres": postgres, "redis": redis, "celery": celery}
        is_healthy = all(check["status"] == "healthy" for check in checks.values())
        return is_healthy, checks

    async def check_postgres(self):
        # noinspection PyBroadException
        try:
            result = await self.db.execute(text("SELECT version_num FROM alembic_version"))
            current_revisions = set(result.scalars().all())

            project_root = Path(__file__).resolve().parents[2]
            alembic_config = Config(str(project_root / "alembic.ini"))
            script_directory = ScriptDirectory.from_config(alembic_config)

            expected_revisions = set(script_directory.get_heads())
            migrations_up_to_date = current_revisions == expected_revisions

            return {
                "status": ("healthy" if migrations_up_to_date else "unhealthy"),
                "database": "connected",
                "migrations": {
                    "status": ("up_to_date" if migrations_up_to_date else "out_of_sync"),
                    "current": sorted(current_revisions),
                    "expected": sorted(expected_revisions),
                },
            }
        except Exception:
            return {"status": "unhealthy", "database": "unavailable_or_error"}

    async def check_redis(self):
        test_key = f"health_check:{uuid.uuid4()}"

        # noinspection PyBroadException
        try:
            await self.redis.set(test_key, "ok", ex=10)

            value = await self.redis.get(test_key)

            if value.decode() != "ok":
                raise RuntimeError("Redis cache read/write failed")

            await self.redis.delete(test_key)

            return {"status": "healthy", "connection": "connected", "cache": "working"}

        except Exception:
            # noinspection PyBroadException
            try:
                await self.redis.delete(test_key)
            except Exception:
                pass

            return {"status": "unhealthy", "connection": "unavailable_or_error", "cache": "not_working"}

    @staticmethod
    async def check_celery():
        # noinspection PyBroadException
        try:
            inspector = celery_app.control.inspect(timeout=2)
            workers = await asyncio.to_thread(inspector.ping)
            if not workers:
                return {"status": "unhealthy", "workers": [], "message": "No responsive Celery workers found"}
            return {"status": "healthy", "workers": list(workers.keys()), "count": len(workers)}
        except Exception:
            return {"status": "unhealthy", "workers": [], "message": "Celery inspection failed"}
