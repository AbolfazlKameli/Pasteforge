from datetime import datetime

from pydantic import BaseModel, EmailStr, UUID4


class UserBase(BaseModel):
    email: EmailStr
    created_at: datetime


class UserOut(UserBase):
    id: UUID4
    updated_at: datetime
