from typing import Annotated

from fastapi import Depends

from pasteforge.services import (
    AnonymousUsageService,
    AuthService,
    IdempotencyService,
    OtpService,
    PasteService,
    TokenPairService,
    UserService,
)

user_service_dep = Annotated[UserService, Depends(UserService)]
token_service_dep = Annotated[TokenPairService, Depends(TokenPairService)]
auth_service_dep = Annotated[AuthService, Depends(AuthService)]
otp_service_dep = Annotated[OtpService, Depends(OtpService)]
anon_usage_service_dep = Annotated[AnonymousUsageService, Depends(AnonymousUsageService)]
paste_service_dep = Annotated[PasteService, Depends(PasteService)]
idempotency_service_dep = Annotated[IdempotencyService, Depends(IdempotencyService)]
