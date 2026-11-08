from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, computed_field

from pasteforge.models import PastesAccessTypes
from pasteforge.schemas.users import UserOut
from pasteforge.schemas.validators import ContentSizeValidator, ExpiresAtValidator, PasswordValidator, get_content_size


class PasteBase(BaseModel):
    content: str
    syntax: str
    access_type: str
    expires_at: datetime


class PasteIn(PasteBase):
    content: ContentSizeValidator
    password: PasswordValidator | None = None
    access_type: PastesAccessTypes
    expires_at: ExpiresAtValidator | None = None

    @computed_field
    @property
    def size_bytes(self) -> int:
        return get_content_size(self.content)


class PasteOut(PasteBase):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID4
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    owner: UserOut | None
