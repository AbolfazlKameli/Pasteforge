import uuid
from datetime import UTC, datetime
from typing import Literal

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import InvalidTokenError
from pasteforge.models import TokenPairStatuses
from pasteforge.repositories import TokenPairRepository


class TokenPairService:
    def __init__(self, db: AsyncSession) -> None:
        self.token_repo = TokenPairRepository(db)

    async def blacklist_by_sid(self, sid: uuid.UUID) -> None:
        await self.token_repo.blacklist_by_sid(sid)

    async def blacklist_by_user_id(self, user_id: uuid.UUID) -> None:
        await self.token_repo.blacklist_by_user_id(user_id)

    async def create_token_pair(self, user_id: uuid.UUID, email: str) -> tuple[str, str]:
        sid = uuid.uuid4()
        now = datetime.now(UTC)

        claims = {"user_id": str(user_id), "email": email, "sid": str(sid)}

        access_token = jwt.encode(
            {**claims, "exp": now + configs.ACCESS_TOKEN_EXPIRE, "token_type": "access"},
            configs.SECRET_KEY,
            algorithm="HS256",
        )

        refresh_token = jwt.encode(
            {**claims, "exp": now + configs.REFRESH_TOKEN_EXPIRE, "token_type": "refresh"},
            configs.SECRET_KEY,
            algorithm="HS256",
        )

        await self.token_repo.create(sid=sid, owner_id=user_id)

        return access_token, refresh_token

    @staticmethod
    def decode_jwt_token(token: str, token_type: Literal["access", "refresh"]) -> dict:
        try:
            payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
        except (JWTError, ValueError, TypeError) as exc:
            raise InvalidTokenError(token_type) from exc

        if not isinstance(payload, dict):
            raise InvalidTokenError(token_type)

        if payload.get("token_type") != token_type:
            raise InvalidTokenError(token_type, "Invalid token type.")

        return payload

    @staticmethod
    def _get_uuid_claim(payload: dict, claim: str, token_type: Literal["access", "refresh"]) -> uuid.UUID:
        try:
            return uuid.UUID(payload[claim])
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidTokenError(token_type) from exc

    def get_token_sid(self, token: str, token_type: Literal["access", "refresh"]) -> uuid.UUID:
        payload = self.decode_jwt_token(token, token_type)
        return self._get_uuid_claim(payload, "sid", token_type)

    async def validate_jwt_token(self, token: str, token_type: Literal["access", "refresh"]) -> uuid.UUID:
        payload = self.decode_jwt_token(token, token_type)

        user_id = self._get_uuid_claim(payload, "user_id", token_type)
        sid = self._get_uuid_claim(payload, "sid", token_type)

        token_pair = await self.token_repo.get_by_sid(sid)

        if token_pair is None or token_pair.status == TokenPairStatuses.blacklisted or token_pair.owner_id != user_id:
            raise InvalidTokenError(token_type, f"{token_type} token is not associated with a valid session.")

        return user_id
