from datetime import datetime
from typing import Self

from pydantic import UUID4, BaseModel, EmailStr, Field, model_validator

from pasteforge.schemas.validators import PasswordValidator


class UserBase(BaseModel):
    email: EmailStr
    created_at: datetime


class UserOut(UserBase):
    id: UUID4
    updated_at: datetime


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class OTPSetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6)
    new_password: PasswordValidator
    confirm_password: PasswordValidator

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class ChangePasswordRequest(BaseModel):
    old_password: PasswordValidator
    new_password: PasswordValidator
    confirm_password: PasswordValidator

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class UserUpdateRequest(BaseModel):
    email: EmailStr


class UserActivationRequest(BaseModel):
    otp_code: str = Field(min_length=6, max_length=6)
    new_email: EmailStr
