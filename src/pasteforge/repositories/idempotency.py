import uuid
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from dependencies import db_dependency
from pasteforge.core.config import configs
from pasteforge.models import IdempotencyRecord, IdempotencyStatus


class IdempotencyRepository:
    def __init__(self, db: db_dependency) -> None:
        self.db = db

    async def get_by_scope_and_key(self, *, scope_key: str, key: uuid.UUID):
        result = await self.db.execute(
            sa.select(IdempotencyRecord)
            .where((IdempotencyRecord.scope_key == scope_key) & (IdempotencyRecord.key == key))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def claim(
        self, *, scope_key: str, key: uuid.UUID, request_hash: str
    ) -> tuple[bool, IdempotencyRecord | None]:
        now = datetime.now(UTC)

        stmt = (
            insert(IdempotencyRecord)
            .values(
                scope_key=scope_key,
                key=key,
                request_hash=request_hash,
                status=IdempotencyStatus.processing,
                expires_at=now + configs.IDEMPOTENCY_KEY_RETENTION,
            )
            .on_conflict_do_nothing(index_elements=[IdempotencyRecord.scope_key, IdempotencyRecord.key])
            .returning(IdempotencyRecord.id)
        )

        result = await self.db.execute(stmt)
        inserted_id = result.scalar_one_or_none()

        if inserted_id is not None:
            record = await self.db.get(IdempotencyRecord, inserted_id)
            return True, record

        existing_record = await self.get_by_scope_and_key(scope_key=scope_key, key=key)

        return False, existing_record

    async def complete(self, *, record_id: UUID, response_status: int, response_body: str) -> None:
        statement = (
            sa.update(IdempotencyRecord)
            .where((IdempotencyRecord.id == record_id) & (IdempotencyRecord.status == IdempotencyStatus.processing))
            .values(status=IdempotencyStatus.completed, response_status=response_status, response_body=response_body)
        )
        await self.db.execute(statement)

    async def delete_expired_by_key(self, *, scope_key: str, key: uuid.UUID):
        now = datetime.now(UTC)
        await self.db.execute(
            sa.delete(IdempotencyRecord).where(
                (IdempotencyRecord.scope_key == scope_key)
                & (IdempotencyRecord.key == key)
                & (IdempotencyRecord.expires_at <= now)
            )
        )

    async def delete_expired(self) -> int:
        now = datetime.now(UTC)
        result = await self.db.execute(sa.delete(IdempotencyRecord).where(IdempotencyRecord.expires_at <= now))
        return result.rowcount
