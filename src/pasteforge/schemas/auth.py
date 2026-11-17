from typing import Self

from fastapi import status
from pydantic import BaseModel, EmailStr, model_validator

from .common import DataSchema, ErrorResponse
from .users import PasswordConfirmationRequest, UserOut
from .validators import OTPCode, PasswordValidator


class UserOTPResponse(BaseModel):
    message: str
    otp_expires_in: int


class UserRegisterRequest(BaseModel):
    email: EmailStr


class UserRegisterResponse(BaseModel):
    message: str
    user: UserOut


class OTPVerifyUserRegisterRequest(PasswordConfirmationRequest):
    email: EmailStr
    password: PasswordValidator
    confirm_password: PasswordValidator
    otp_code: OTPCode

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: PasswordValidator


auth_responses = {
    status.HTTP_401_UNAUTHORIZED: {"model": DataSchema[ErrorResponse], "description": "Authentication failed."},
    status.HTTP_403_FORBIDDEN: {"model": DataSchema[ErrorResponse], "description": "Not Permitted."},
}
