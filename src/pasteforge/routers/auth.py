import logging

from fastapi import APIRouter, status, HTTPException

from src.dependencies import db_dependency
from src.pasteforge.core.config import configs
from src.pasteforge.repositories.users import check_email_exists
from src.pasteforge.schemas.auth import UserOTPResponse, UserRegisterRequest
from src.pasteforge.schemas.common import DataSchema, ErrorResponse
from src.pasteforge.services.auth import check_blacklist_for_user, generate_and_send_otp

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
