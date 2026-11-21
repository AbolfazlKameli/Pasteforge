import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from redis_fastapi import rate_limit

from pasteforge.api.dependencies import auth_service_dep, otp_service_dep, token_service_dep, user_service_dep
from pasteforge.core.config import configs
from pasteforge.core.exceptions import UserAlreadyExistsError, too_many_requests_error
from pasteforge.core.security import generate_csrf_token
from pasteforge.schemas.auth import (
    OTPVerifyUserRegisterRequest,
    UserLoginRequest,
    UserOTPResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    auth_responses,
)
from pasteforge.schemas.common import DataSchema, ErrorResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str) -> None:
    secure = not configs.DEBUG

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        path="/api/v1/auth/refresh",
        max_age=86400,
        samesite="lax",
    )
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=secure, path="/", max_age=900, samesite="lax"
    )
    response.set_cookie(
        key="csrf_token", value=csrf_token, httponly=False, secure=secure, path="/", max_age=86400, samesite="lax"
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token", path="/api/v1/auth/refresh", secure=not configs.DEBUG, httponly=True, samesite="lax"
    )
    response.delete_cookie(key="access_token", path="/", secure=not configs.DEBUG, httponly=True, samesite="lax")
    response.delete_cookie(key="csrf_token", path="/", secure=not configs.DEBUG, httponly=False, samesite="lax")


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[UserOTPResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Email already exists."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def request_otp_to_register(
    register_data: UserRegisterRequest, auth_service: auth_service_dep, user_service: user_service_dep
):
    email = str(register_data.email)

    await auth_service.check_blacklist_for_user(email)

    if await user_service.exists_by_email(email):
        raise UserAlreadyExistsError()

    await auth_service.generate_and_send_otp(email)

    logger.info("Registration OTP sent successfully")

    return {
        "data": {
            "message": "Verification email sent.",
            "otp_valid_time": int(configs.OTP_SETTINGS.EXPIRATION_TIME.total_seconds()),
        }
    }


@router.post(
    "/register/verify",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[UserRegisterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Email already exists."},
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "OTP verification failed."},
    },
)
async def verify_otp_code(
    request_data: OTPVerifyUserRegisterRequest, otp_service: otp_service_dep, user_service: user_service_dep
):
    email = str(request_data.email)

    otp = await otp_service.validate_otp(email, request_data.otp_code)

    user = await user_service.create_user(email, request_data.password.get_secret_value())

    await otp_service.delete_otp(otp)

    logger.info("User registration completed successfully")

    return {"data": {"message": "User registered successfully.", "user": user}}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Email or password is incorrect.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def user_login(
    login_data: UserLoginRequest, response: Response, user_service: user_service_dep, token_service: token_service_dep
):
    email = str(login_data.email)

    user = await user_service.authenticate_user_by_email(email, login_data.password.get_secret_value())

    access_token, refresh_token = await token_service.create_token_pair(user.id, email)

    csrf_token = generate_csrf_token()

    _set_auth_cookies(response, access_token, refresh_token, csrf_token)

    logger.info("User login successful")

    return {"data": {"message": "User logged in successfully."}}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid authentication token.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def user_logout(
    response: Response, token_service: token_service_dep, access_token: Annotated[str, Cookie(alias="access_token")]
):
    token_sid = token_service.get_token_sid(access_token, "access")
    await token_service.blacklist_by_sid(token_sid)

    _clear_auth_cookies(response)

    logger.info("User logout successful")

    return {"data": {"message": "User logged out successfully."}}


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid refresh token."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
        **auth_responses,
    },
)
async def refresh_auth_token(
    response: Response,
    token_service: token_service_dep,
    user_service: user_service_dep,
    refresh_token: Annotated[str, Cookie(alias="refresh_token")],
):
    user_id = await token_service.validate_jwt_token(refresh_token, "refresh")
    user = await user_service.get_active_user_by_id(user_id)

    token_sid = token_service.get_token_sid(refresh_token, "refresh")
    await token_service.blacklist_by_sid(token_sid)

    access_token, new_refresh_token = await token_service.create_token_pair(user.id, user.email)

    csrf_token = generate_csrf_token()

    _set_auth_cookies(response, access_token, new_refresh_token, csrf_token)

    logger.info("Authentication token refresh completed successfully")

    return {"data": {"message": "Tokens refreshed successfully."}}
