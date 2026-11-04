import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from pasteforge.api.dependencies import auth_service_dep, token_service_dep, user_service_dep
from pasteforge.api.dependencies.services import otp_service_dep
from pasteforge.core.config import configs
from pasteforge.core.exceptions import UserAlreadyExistsError
from pasteforge.schemas.auth import (
    OtpVerifyUserRegisterRequest,
    UserLoginRequest,
    UserOTPResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    auth_responses,
)
from pasteforge.schemas.common import DataSchema, ErrorResponse, SuccessResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _set_auth_cookies(access: str, refresh: str, response: Response) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not configs.DEBUG,
        path="/api/v1/auth/refresh",
        max_age=86400,
        samesite="lax",
    )

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=not configs.DEBUG,
        path="/",
        max_age=900,
        samesite="lax",
    )


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataSchema[UserOTPResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email already exists.",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when too many requests occurs.",
        },
    },
)
async def request_otp_to_register(
        register_data: UserRegisterRequest, auth_service: auth_service_dep, user_service: user_service_dep
):
    email = str(register_data.email)

    await auth_service.check_blacklist_for_user(email)

    if await user_service.user_exists_with_email(email):
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
    response_model=DataSchema[UserRegisterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email already exists.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when OTP verification failed.",
        },
    },
)
async def verify_otp_code(
        request_data: OtpVerifyUserRegisterRequest, otp_service: otp_service_dep, user_service: user_service_dep
):
    otp_code = request_data.otp_code
    email = str(request_data.email)

    otp = await otp_service.validate_otp(email, otp_code)

    user = await user_service.create_user(email, request_data.password.get_secret_value())

    await otp_service.delete_otp(otp)

    logger.info("User registration completed successfully")

    return {"data": {"message": "User Registered successfully.", "user": user}}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email or password is incorrect.",
        }
    },
)
async def user_login(
        login_data: UserLoginRequest, user_service: user_service_dep, token_service: token_service_dep,
        response: Response
):
    email = str(login_data.email)
    user = await user_service.authenticate_user_by_email(email, login_data.password.get_secret_value())

    # noinspection PyTypeChecker
    access, refresh = await token_service.create_token_pair(user.id, email)

    _set_auth_cookies(access, refresh, response)

    logger.info("User login successful")

    return {"data": {"message": "User logged in Successfully."}}


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid refresh token."},
        **auth_responses,
    },
)
async def refresh_auth_token(
        token_service: token_service_dep,
        user_service: user_service_dep,
        refresh_token: Annotated[str, Cookie(alias="refresh_token")],
        response: Response,
):
    user_id = await token_service.validate_jwt_token(refresh_token, "refresh")
    user = await user_service.get_active_user_by_id(user_id)

    user_id = user.id
    user_email = user.email

    await token_service.blacklist_token_pair_by_sid(token_service.get_token_sid(refresh_token, "refresh"))

    # noinspection PyTypeChecker
    access, refresh = await token_service.create_token_pair(user_id, user_email)

    _set_auth_cookies(access, refresh, response)

    logger.info("Authentication token refresh completed successfully")

    return {"data": {"message": "Token Refreshed successfully."}}
