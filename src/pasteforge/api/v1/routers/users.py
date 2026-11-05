import logging

from fastapi import APIRouter, Depends, status
from redis_fastapi import rate_limit

from pasteforge.api.dependencies import active_user_dep, auth_service_dep, user_service_dep
from pasteforge.api.dependencies.services import otp_service_dep, token_service_dep
from pasteforge.core.exceptions import NotFoundError, too_many_requests_error
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
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[UserOut],
    responses={**auth_responses},
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
)
async def get_user_profile(user: active_user_dep):
    return {"data": user}


@router.put(
    "/profile",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email or username"},
        **auth_responses,
    },
)
async def update_user_profile(
    update_request: UserUpdateRequest,
    user: active_user_dep,
    user_service: user_service_dep,
    auth_service: auth_service_dep,
):
    update_request_dict = update_request.model_dump(exclude_unset=True)
    email = update_request_dict.get("email")

    await auth_service.check_blacklist_for_user(email)

    email_changed = await user_service.update_user_data(user.id, **update_request_dict)
    if email_changed:
        await auth_service.generate_and_send_otp(email)

    return {"data": {"message": "Otp code sent to your new email address."}}


@router.post(
    "/profile/email/verify",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Invalid or expired OTP code."}
    },
)
async def verify_user_email(
    activation_request: UserActivationRequest,
    user: active_user_dep,
    otp_service: otp_service_dep,
    user_service: user_service_dep,
    token_service: token_service_dep,
):
    otp_code = activation_request.otp_code
    new_email = str(activation_request.new_email)
    user_id = user.id

    otp = await otp_service.validate_otp(new_email, otp_code)
    await user_service.update_user_email(user.id, email=new_email)
    await token_service.blacklist_token_pair_by_user_id(user_id)
    await otp_service.delete_otp(otp)

    logger.info("User email verification completed successfully")

    return {"data": {"message": "Your account has been verified successfully."}}


@router.delete(
    "/profile",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    responses={**auth_responses},
)
async def delete_user_profile(user: active_user_dep, user_service: user_service_dep):
    await user_service.delete_user(user)


@router.post(
    "/password/reset",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email address."},
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Blacklisted email."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def request_otp_to_reset_password(
    reset_data: ResetPasswordRequest, auth_service: auth_service_dep, user_service: user_service_dep
):
    email = str(reset_data.email)

    await auth_service.check_blacklist_for_user(email)

    user = await user_service.get_user_by_email(email)
    if user is None:
        return {"data": {"message": "Otp code sent for reset password."}}

    await auth_service.generate_and_send_otp(email)

    logger.info("Password reset OTP request completed successfully")

    return {"data": {"message": "Otp code sent for reset password."}}


@router.post(
    "/password/set",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Invalid email address."},
        status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Invalid OTP code."},
    },
)
async def set_password(
    validated_data: OTPSetPasswordRequest,
    otp_service: otp_service_dep,
    user_service: user_service_dep,
    token_service: token_service_dep,
):
    otp_code = validated_data.otp_code
    email = str(validated_data.email)

    otp = await otp_service.validate_otp(email, otp_code)

    user = await user_service.get_user_by_email(email)
    if user is None:
        raise NotFoundError()

    await user_service.change_password(user, validated_data.new_password.get_secret_value())

    await token_service.blacklist_token_pair_by_user_id(user.id)

    await otp_service.delete_otp(otp)

    logger.info("User password reset completed successfully")

    send_notification_email.delay(email, "Your Pasteforge Password Has Been Changed", password_change_message)

    return {"data": {"message": "Your password has been changed successfully."}}


@router.post(
    "/password/change",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("1/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": DataSchema[ErrorResponse], "description": "Incorrect password."},
        **auth_responses,
    },
)
async def change_user_password(
    change_request: ChangePasswordRequest,
    user: active_user_dep,
    token_service: token_service_dep,
    user_service: user_service_dep,
):
    email = user.email
    password = change_request.old_password.get_secret_value()
    new_password = change_request.new_password.get_secret_value()

    await user_service.change_password(user, new_password, password)
    await token_service.blacklist_token_pair_by_user_id(user.id)

    logger.info("User password changed successfully")

    send_notification_email.delay(email, "Your Pasteforge Password Has Been Changed", password_change_message)

    return {"data": {"message": "Your password has been changed successfully."}}
