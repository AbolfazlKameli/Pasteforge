from typing import Self

from fastapi import status
from pydantic import BaseModel, EmailStr, Field, model_validator

from .common import DataSchema, ErrorResponse
from .users import UserOut
from .validators import PasswordValidator


class UserOTPResponse(BaseModel):
    message: str
    otp_valid_time: int


class UserRegisterRequest(BaseModel):
    email: EmailStr


class UserRegisterResponse(BaseModel):
    message: str
    user: UserOut


class OtpVerifyUserRegisterRequest(BaseModel):
    email: EmailStr
    password: PasswordValidator
    confirm_password: PasswordValidator
    otp_code: str = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class UserTokenResponse(BaseModel):
    message: str
    access_token: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: PasswordValidator


auth_responses = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": DataSchema[ErrorResponse],
        "description": "Authentication failed."
    },
    status.HTTP_403_FORBIDDEN: {
        "model": DataSchema[ErrorResponse],
        "description": "Not Permitted."
    }
}
