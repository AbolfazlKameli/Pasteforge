import logging

from fastapi import APIRouter, HTTPException, status

from dependencies import db_dependency
from pasteforge.repositories.users import get_user_by_email
from pasteforge.schemas.auth import auth_responses
from pasteforge.schemas.common import DataSchema, ErrorResponse, SuccessResponse
from pasteforge.schemas.users import ResetPasswordRequest, UserOut
from pasteforge.services.auth import check_blacklist_for_user, generate_and_send_otp, user_dependency

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get(
    "/profile", status_code=status.HTTP_200_OK, response_model=DataSchema[UserOut], responses={**auth_responses}
)
async def get_user_profile(user: user_dependency):
    return {"data": user}


@router.post(
    "/password/reset",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email address."},
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Blacklisted email."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def request_otp_to_reset_password(db: db_dependency, reset_data: ResetPasswordRequest):
    email = str(reset_data.email)

    message, throttle_wait = await check_blacklist_for_user(db, email)
    if message is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message, headers={"Retry-After": str(throttle_wait)}
        )

    user = await get_user_by_email(db, email)
    if user is None:
        return {"data": {"message": "Otp code sent for reset password."}}

    await generate_and_send_otp(db, email)

    logger.info("Password reset OTP request completed successfully")

    return {"data": {"message": "Otp code sent for reset password."}}
