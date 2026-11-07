from datetime import datetime

from pydantic import BaseModel, computed_field

from pasteforge.schemas.users import UserOut
from pasteforge.schemas.validators import ContentSizeValidator, PasswordValidator, get_content_size


class PasteBase(BaseModel):
    content: ContentSizeValidator
    syntax: str
    access_type: str
    expires_at: datetime


class PasteIn(PasteBase):
    password: PasswordValidator | None

    @computed_field
    @property
    def size_bytes(self) -> int:
        return get_content_size(self.content)


class PasteOut(PasteBase):
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    owner: UserOut
