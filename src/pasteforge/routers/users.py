import logging

from fastapi import APIRouter, HTTPException, status

from dependencies import db_dependency
from pasteforge.repositories.auth import get_otp
from pasteforge.repositories.users import check_email_exists, get_user_by_email, update_user
from pasteforge.schemas.auth import auth_responses
from pasteforge.schemas.common import DataSchema, ErrorResponse, SuccessResponse
from pasteforge.schemas.users import (
    ChangePasswordRequest,
    OTPSetPasswordRequest,
    ResetPasswordRequest,
    UserActivationRequest,
    UserOut,
    UserUpdateRequest,
)
from pasteforge.services.auth import check_blacklist_for_user, generate_and_send_otp, user_dependency
from pasteforge.tasks import send_notification_email

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

password_change_message = """
    Hi, The password for your Pasteforge account was successfully changed.
    If you made this change, no further action is required.
    If you did not change your password, your account may be at risk.
    Please reset your password immediately and contact our support team if you need assistance.
    For your security, never share your password with anyone.
    Best regards,  
    The Pasteforge Team
"""


@router.get(
    "/profile", status_code=status.HTTP_200_OK, response_model=DataSchema[UserOut], responses={**auth_responses}
)
async def get_user_profile(user: user_dependency):
    return {"data": user}


@router.put(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email or username"},
        **auth_responses,
    },
)
async def update_user_profile(db: db_dependency, update_request: UserUpdateRequest, user: user_dependency):
    update_request_dict = update_request.model_dump(exclude_unset=True)
    email = update_request_dict.pop("email", None)

    if await check_email_exists(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already taken.")

    await update_user(db, user.id, **update_request_dict)

    if email is not None:
        await generate_and_send_otp(db, email)

    return {"data": {"message": "Otp code sent to your new email address."}}


@router.post(
    "/profile/email/verify",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Invalid or expired OTP code."}
    },
)
async def verify_user_email(db: db_dependency, activation_request: UserActivationRequest, user: user_dependency):
    otp_code = activation_request.otp_code
    new_email = str(activation_request.new_email)

    otp_obj = await get_otp(db, new_email)

    if otp_obj is None or not otp_obj.verify_otp(otp_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired OTP code.")

    await update_user(db, user.id, email=new_email)

    await db.delete(otp_obj)
    await db.commit()

    logger.info("User email verification completed successfully")

    return {"data": {"message": "Your account has been verified successfully."}}


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT, responses={**auth_responses})
async def delete_user_profile(db: db_dependency, user: user_dependency):
    await db.delete(user)
    await db.commit()


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


@router.post(
    "/password/set",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email address."},
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Invalid OTP code."},
    },
)
async def set_password(db: db_dependency, validated_data: OTPSetPasswordRequest):
    otp_code = validated_data.otp_code
    email = str(validated_data.email)

    otp_obj = await get_otp(db, email)

    if otp_obj is None or not otp_obj.verify_otp(otp_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired OTP code.")

    user = await get_user_by_email(db, email)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.set_password(validated_data.new_password.get_secret_value())
    db.add(user)
    await db.delete(otp_obj)
    await db.commit()

    logger.info("User password reset completed successfully")

    send_notification_email.delay(email, "Your Pasteforge Password Has Been Changed", password_change_message)

    return {"data": {"message": "Your password has been changed successfully."}}


@router.post(
    "/password/change",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Incorrect password."},
        **auth_responses,
    },
)
async def change_user_password(db: db_dependency, change_request: ChangePasswordRequest, user: user_dependency):
    email = user.email
    password = change_request.old_password.get_secret_value()
    new_password = change_request.new_password.get_secret_value()

    if not user.verify_password(password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password.")

    user.set_password(new_password)
    db.add(user)
    await db.commit()

    logger.info("User password changed successfully")

    send_notification_email.delay(email, "Your Pasteforge Password Has Been Changed", password_change_message)

    return {"data": {"message": "Your password has been changed successfully."}}
