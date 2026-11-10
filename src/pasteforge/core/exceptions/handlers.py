from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from redis_fastapi import RateLimitResult
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from pasteforge.core.exceptions import AuthenticationError
from pasteforge.core.exceptions.exceptions import AppException, InvalidTokenError, TooManyRequestsError


async def too_many_requests_error(request: Request, result: RateLimitResult):
    return JSONResponse(
        content={"data": {"errors": f"Too many requests. retry after {result.retry_after} seconds."}},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(content={"data": {"errors": exc.detail}}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_exception_handler(request: Request, exc: InvalidTokenError):
        headers = {"WWW-Authenticate": 'Bearer error="missing_access_token"'}
        return JSONResponse(content={"data": {"errors": exc.message}}, status_code=exc.status_code, headers=headers)

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
        errors = [{"loc": error["loc"], "msg": error["msg"]} for error in exc.errors()]
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"data": {"errors": errors}})
