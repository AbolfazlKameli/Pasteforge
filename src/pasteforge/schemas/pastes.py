from typing import Self

from pydantic import UUID4, AwareDatetime, BaseModel, ConfigDict, Field, computed_field, model_validator

from pasteforge.models import PastesAccessTypes
from pasteforge.schemas.users import UserOut
from pasteforge.schemas.validators import ContentSizeValidator, ExpiresAtValidator, PasswordValidator, get_content_size


class PasteBase(BaseModel):
    content: str
    syntax: str
    access_type: PastesAccessTypes
    expires_at: AwareDatetime


class PasteIn(PasteBase):
    content: ContentSizeValidator
    password: PasswordValidator | None = None
    expires_at: ExpiresAtValidator | None = None

    @model_validator(mode="after")
    def validate_password_access(self) -> Self:
        is_protected = self.access_type == PastesAccessTypes.password_protected

        if is_protected and self.password is None:
            raise ValueError("Password is required for password-protected pastes.")

        if not is_protected and self.password is not None:
            raise ValueError("Password is only allowed for password-protected pastes.")

        return self

    @computed_field
    @property
    def size_bytes(self) -> int:
        return get_content_size(self.content)


class PasteOut(PasteBase):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID4
    size_bytes: int = Field(gt=0)
    created_at: AwareDatetime
    updated_at: AwareDatetime
    owner: UserOut | None


class ProtectedPasteRequest(BaseModel):
    password: PasswordValidator


class PasteUpdateRequest(BaseModel):
    content: ContentSizeValidator | None = None
    syntax: str | None = None
    access_type: PastesAccessTypes | None = None
    expires_at: ExpiresAtValidator | None = None

    # Current password, used for authorization.
    password: PasswordValidator | None = None

    # New password, used when setting/changing protection.
    new_password: PasswordValidator | None = None

    @model_validator(mode="after")
    def validate_update_data(self) -> Self:
        editable_fields = ("content", "syntax", "access_type", "expires_at", "new_password")

        if not any(field in self.model_fields_set for field in editable_fields):
            raise ValueError("At least one field must be provided.")

        for field in ("content", "syntax", "access_type", "expires_at"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")

        return self


class PasteExpiryRequest(BaseModel):
    password: PasswordValidator | None = None
    expires_at: ExpiresAtValidator


class PasteDeleteRequest(BaseModel):
    password: PasswordValidator | None = None
