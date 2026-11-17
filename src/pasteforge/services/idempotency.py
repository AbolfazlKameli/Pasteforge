import hashlib
import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.exceptions import IdempotencyConflictError, IdempotencyInProgressError
from pasteforge.core.security import hash_ip
from pasteforge.models import IdempotencyStatus
from pasteforge.repositories import IdempotencyRepository


class IdempotencyService:
    def __init__(self, db: AsyncSession):
        self.idempotency_repo = IdempotencyRepository(db)

    @staticmethod
    def build_scope_key(user_id: uuid.UUID | None, client_ip: str | None) -> str:
        if user_id is None:
            return f"anon:{hash_ip(client_ip)}"
        return f"user:{user_id}"

    @staticmethod
    def generate_request_hash(*, method: str, path: str, payload: Any) -> str:
        normalized_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
        canonical_request = {"method": method.upper(), "path": path, "payload": normalized_payload}
        serialized = json.dumps(canonical_request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def claim_idempotency(
            self, *, scope_key: str, idempotency_key: uuid.UUID, request_hash: str
    ) -> tuple[str | None, uuid.UUID]:
        await self.idempotency_repo.delete_expired_by_key(scope_key=scope_key, key=idempotency_key)

        is_new, record = await self.idempotency_repo.claim(
            scope_key=scope_key, key=idempotency_key, request_hash=request_hash
        )

        if record is None:
            raise RuntimeError("Idempotency record could not be loaded.")

        if is_new:
            return record.response_body, record.id

        if record.request_hash != request_hash:
            raise IdempotencyConflictError("Idempotency key was used with another request.")

        if record.status != IdempotencyStatus.completed:
            raise IdempotencyInProgressError("Request is still being processed.")

        return record.response_body, record.id

    async def complete_idempotency(self, *, record_id: uuid.UUID, response_status: int, response_body: str) -> None:
        await self.idempotency_repo.complete(
            record_id=record_id, response_status=response_status, response_body=response_body
        )
