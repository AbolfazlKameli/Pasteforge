import uuid
from typing import Annotated

from fastapi import Cookie, Depends

from pasteforge.api.dependencies.services import token_service_dep, user_service_dep
from pasteforge.core.exceptions import AuthenticationError, ForbiddenError, InvalidTokenError
from pasteforge.models import User


async def jwt_cookie(access_token: Annotated[str, Cookie()], token_service: token_service_dep) -> uuid.UUID:
    if not access_token:
        raise InvalidTokenError("access", "Access token is missing.")

    return await token_service.validate_jwt_token(access_token, token_type="access")


async def get_authenticated_user(
        user_id: Annotated[uuid.UUID, Depends(jwt_cookie)], user_service: user_service_dep
) -> User | None:
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise AuthenticationError("Authentication failed, invalid user.")
    return user


async def get_active_user(user: Annotated[User, Depends(get_authenticated_user)]) -> User | None:
    if not user.is_active:
        raise ForbiddenError("Inactive user account.")

    return user


active_user_dep = Annotated[User, Depends(get_active_user)]
