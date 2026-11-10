from typing import Annotated

from fastapi import Depends

from dependencies import db_dependency
from pasteforge.api.dependencies.caches import PasteCacheDep
from pasteforge.services import (
    AnonymousUsageService,
    AuthService,
    OtpService,
    PasteService,
    TokenPairService,
    UserService,
)


def get_user_service(db: db_dependency) -> UserService:
    return UserService(db)


def get_token_service(db: db_dependency) -> TokenPairService:
    return TokenPairService(db)


def get_auth_service(db: db_dependency) -> AuthService:
    return AuthService(db)


def get_otp_service(db: db_dependency) -> OtpService:
    return OtpService(db)


def get_anon_usage_service(db: db_dependency) -> AnonymousUsageService:
    return AnonymousUsageService(db)


def get_paste_service(db: db_dependency, cache: PasteCacheDep) -> PasteService:
    return PasteService(db, cache)


user_service_dep = Annotated[UserService, Depends(get_user_service)]
token_service_dep = Annotated[TokenPairService, Depends(get_token_service)]
auth_service_dep = Annotated[AuthService, Depends(get_auth_service)]
otp_service_dep = Annotated[OtpService, Depends(get_otp_service)]
anon_usage_service_dep = Annotated[AnonymousUsageService, Depends(get_anon_usage_service)]
paste_service_dep = Annotated[PasteService, Depends(get_paste_service)]
