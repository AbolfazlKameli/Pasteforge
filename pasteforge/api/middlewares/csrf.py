from typing import ClassVar

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from pasteforge.core.exceptions import ForbiddenError
from pasteforge.core.security import validate_csrf_token


class CSRFMiddleware(BaseHTTPMiddleware):
    SAFE_METHODS: ClassVar[set[str]] = {"GET", "HEAD", "OPTIONS", "TRACE"}
    EXEMPT_PATHS: ClassVar[set[str]] = {"/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/register-verify"}

    AUTH_COOKIE_NAMES = ("access_token", "refresh_token")

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        if not any(name in request.cookies for name in self.AUTH_COOKIE_NAMES):
            return await call_next(request)

        try:
            validate_csrf_token(request)
        except ForbiddenError as exc:
            return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code)

        return await call_next(request)
