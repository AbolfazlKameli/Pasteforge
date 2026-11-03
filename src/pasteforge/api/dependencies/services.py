from typing import Annotated

from fastapi import Depends

from dependencies import db_dependency
from pasteforge.services import OtpService
from pasteforge.services.auth import AuthService
from pasteforge.services.token import TokenPairService
from pasteforge.services.users import UserService


def get_user_service(db: db_dependency) -> UserService:
    return UserService(db)


def get_token_service(db: db_dependency) -> TokenPairService:
    return TokenPairService(db)


def get_auth_service(db: db_dependency) -> AuthService:
    return AuthService(db)


def get_otp_service(db: db_dependency) -> OtpService:
    return OtpService(db)


user_service_dep = Annotated[UserService, Depends(get_user_service)]
token_service_dep = Annotated[TokenPairService, Depends(get_token_service)]
auth_service_dep = Annotated[AuthService, Depends(get_auth_service)]
otp_service_dep = Annotated[OtpService, Depends(get_otp_service)]
