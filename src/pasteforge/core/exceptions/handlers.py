from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from pasteforge.core.exceptions.exceptions import AppException, InvalidTokenError, TooManyRequestsError


def _safe_serialize_value(value):
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _safe_serialize_value(v) for k, v in value.items()}
    return str(value)


def _sanitize_validation_errors(errors: Sequence[Any]) -> list[dict]:
    sanitized = []
    for error in errors:
        safe_error = dict(error)
        if "ctx" in safe_error and isinstance(safe_error["ctx"], dict):
            safe_ctx = {}
            for k, v in safe_error["ctx"].items():
                safe_ctx[k] = _safe_serialize_value(v)
            safe_error["ctx"] = safe_ctx
        if "input" in safe_error:
            safe_error["input"] = _safe_serialize_value(safe_error["input"])
        sanitized.append(safe_error)
    return sanitized


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(content={"data": {"errors": exc.detail}}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code)

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_exception_handler(request: Request, exc: InvalidTokenError):
        headers = {
            "WWW-Authenticate": 'Bearer error="invalid_token"',
            "X-Auth-Error": f"{exc.token_type}_token_invalid",
        }
        return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code, headers=headers)

    @app.exception_handler(TooManyRequestsError)
    async def too_many_requests_error(request: Request, exc: TooManyRequestsError):
        headers = {}
        if exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code, headers=headers)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            content={"data": {"errors": "Unexpected error."}}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"data": {"errors": exc.errors()}}
        )
