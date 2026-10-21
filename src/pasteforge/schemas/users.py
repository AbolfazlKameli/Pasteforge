from datetime import datetime

from pydantic import UUID4, BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    created_at: datetime


class UserOut(UserBase):
    id: UUID4
    updated_at: datetime


class ResetPasswordRequest(BaseModel):
    email: EmailStr
