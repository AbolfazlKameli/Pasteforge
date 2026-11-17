import uuid
from typing import Annotated

from fastapi import Header

idempotency_key_dep = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]
