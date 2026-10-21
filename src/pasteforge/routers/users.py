from fastapi import APIRouter, status

from pasteforge.schemas.auth import auth_responses
from pasteforge.schemas.common import DataSchema
from pasteforge.schemas.users import UserOut
from pasteforge.services.auth import user_dependency

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/profile", status_code=status.HTTP_200_OK, response_model=DataSchema[UserOut], responses={**auth_responses}
)
async def get_user_profile(user: user_dependency):
    return {"data": user}
