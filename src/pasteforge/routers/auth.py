import logging

from fastapi import APIRouter, status, HTTPException

from src.dependencies import db_dependency
from src.pasteforge.core.config import configs
from src.pasteforge.repositories.auth import get_otp
from src.pasteforge.repositories.users import check_email_exists
from src.pasteforge.schemas.auth import (
    UserOTPResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    OtpVerifyUserRegisterRequest
)
from src.pasteforge.schemas.common import DataSchema, ErrorResponse
from src.pasteforge.services.auth import check_blacklist_for_user, generate_and_send_otp
from src.pasteforge.services.users import register_user

router = APIRouter(prefix='/auth', tags=['auth'])
logger = logging.getLogger(__name__)


@router.post(
    '/register',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataSchema[UserOTPResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when email already exists.'
        },
        status.HTTP_403_FORBIDDEN: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when user is blacklisted.'
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when too many requests occurs.'
        }
    }
)
async def request_otp_to_register(register_data: UserRegisterRequest, db: db_dependency):
    email = str(register_data.email)

    message, throttle_wait = await check_blacklist_for_user(db, email)
    if message is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={'Retry-After': str(throttle_wait)}
        )

    if await check_email_exists(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already exists. if you believe your account is deactivated, call support.'
        )

    await generate_and_send_otp(db, email)

    logger.info("Registration OTP sent successfully")

    return {
        'data': {
            'message': 'Verification email sent.',
            'otp_valid_time': int(configs.OTP_SETTINGS.EXPIRATION_TIME.total_seconds())
        }
    }


@router.post(
    '/register/verify',
    status_code=status.HTTP_201_CREATED,
    response_model=DataSchema[UserRegisterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when email already exists.'
        },
        status.HTTP_403_FORBIDDEN: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when OTP verification failed.'
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'model': DataSchema[ErrorResponse],
            'description': 'Error when something unexpected happened.'
        }
    }
)
async def verify_otp_code(request_data: OtpVerifyUserRegisterRequest, db: db_dependency):
    otp_code = request_data.otp_code
    email = str(request_data.email)
    otp_obj = await get_otp(db, email)

    if otp_obj is None or (not otp_obj.verify_otp(otp_code)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid or expired OTP code.')

    if await check_email_exists(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or email already taken.')

    try:
        password = request_data.password.get_secret_value()
        user = await register_user(db, password=password, email=email)
    except (ValueError, RuntimeError):
        logger.exception("User registration failed during OTP verification")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error.')

    await db.delete(otp_obj)
    await db.commit()

    await db.refresh(user)

    logger.info("User registration completed successfully")

    return {
        'data': {
            'message': 'User Registered successfully.',
            'user': user
        }
    }
