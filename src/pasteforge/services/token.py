import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from pasteforge.core.config import configs
from pasteforge.core.exceptions import InvalidTokenError
from pasteforge.models import TokenObtainPair
from pasteforge.repositories.token import TokenPairRepository


class TokenPairService:
    def __init__(self, db: AsyncSession):
        self.token_repo = TokenPairRepository(db)

    async def get_blacklist_by_sid(self, sid: uuid.UUID) -> TokenObtainPair:
        return await self.token_repo.get_blacklisted_by_sid(sid)

    async def blacklist_token_pair_by_sid(self, sid: uuid.UUID) -> None:
        await self.token_repo.blacklist_token_pair_by_sid(sid)

    async def blacklist_token_pair_by_user_id(self, user_id: uuid.UUID) -> None:
        await self.token_repo.blacklist_token_pair_by_user_id(user_id)

    async def is_token_pair_exists(self, sid: uuid.UUID) -> bool:
        return await self.token_repo.is_pair_exists(sid)

    async def create_token_pair(self, user_id: uuid.UUID, email: str) -> tuple[str, str]:
        sid = uuid.uuid4()
        payload = {"user_id": str(user_id), "email": email, "sid": str(sid)}

        access_exp = datetime.now(UTC) + timedelta(minutes=15)
        payload.update({"exp": access_exp, "token_type": "access"})
        access_token = jwt.encode(payload, configs.SECRET_KEY, algorithm="HS256")

        refresh_exp = datetime.now(UTC) + timedelta(hours=24)
        payload.update({"exp": refresh_exp, "token_type": "refresh"})
        refresh_token = jwt.encode(payload, configs.SECRET_KEY, algorithm="HS256")

        await self.token_repo.create(sid, user_id)

        return access_token, refresh_token

    @staticmethod
    def decode_jwt_token(token: str, token_type: Literal["access", "refresh"]) -> dict:
        try:
            payload = jwt.decode(token, configs.SECRET_KEY, algorithms=["HS256"])
            jwt_type: str = payload.get("token_type")
        except (JWTError, ValueError, TypeError, KeyError) as e:
            raise InvalidTokenError(token_type) from e

        if jwt_type != token_type:
            raise InvalidTokenError(token_type, "Invalid token type.")

        return payload

    def get_token_sid(self, token: str, token_type: Literal["access", "refresh"]) -> uuid.UUID:
        payload = self.decode_jwt_token(token, token_type)
        return uuid.UUID(payload["sid"])

    async def validate_jwt_token(self, token: str, token_type: Literal["access", "refresh"]) -> uuid.UUID:
        payload = self.decode_jwt_token(token, token_type)
        user_id = uuid.UUID(payload.get("user_id"))
        sid = uuid.UUID(payload.get("sid"))

        if not await self.is_token_pair_exists(sid):
            raise InvalidTokenError(token_type, f"{token_type} token is not associated with a valid session.")

        blacklist = await self.get_blacklist_by_sid(sid)
        if blacklist is not None:
            raise InvalidTokenError(token_type, f"{token_type} token is not associated with a valid session.")

        return user_id
