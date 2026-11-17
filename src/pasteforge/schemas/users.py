from typing import Self

from pydantic import UUID4, AwareDatetime, BaseModel, ConfigDict, EmailStr, model_validator

from pasteforge.schemas.validators import OTPCode, PasswordValidator


class UserBase(BaseModel):
    email: EmailStr


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID4
    updated_at: AwareDatetime
    created_at: AwareDatetime


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class PasswordConfirmationRequest(BaseModel):
    new_password: PasswordValidator
    confirm_password: PasswordValidator

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class OTPSetPasswordRequest(PasswordConfirmationRequest):
    email: EmailStr
    otp_code: OTPCode


class ChangePasswordRequest(PasswordConfirmationRequest):
    old_password: PasswordValidator


class UserUpdateRequest(BaseModel):
    email: EmailStr


class UserActivationRequest(BaseModel):
    otp_code: OTPCode
    new_email: EmailStr
