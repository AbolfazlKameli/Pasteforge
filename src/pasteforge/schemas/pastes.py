from datetime import datetime

from pydantic import BaseModel

from pasteforge.schemas.users import UserOut
from pasteforge.schemas.validators import PasswordValidator


class PasteBase(BaseModel):
    content: str
    syntax: str
    size_bytes: int
    access_type: str
    expires_at: datetime


class PasteIn(PasteBase):
    password: PasswordValidator | None


class PasteOut(PasteBase):
    created_at: datetime
    updated_at: datetime
    owner: UserOut
