import uuid

from fastapi import APIRouter, Depends, Request, status
from redis_fastapi import rate_limit

from pasteforge.api.dependencies import active_user_dep, anon_usage_service_dep, optional_user_dep, paste_service_dep
from pasteforge.core.exceptions import too_many_requests_error
from pasteforge.schemas.auth import auth_responses
from pasteforge.schemas.common import DataSchema, ErrorResponse
from pasteforge.schemas.pastes import PasteIn, PasteOut

router = APIRouter(prefix="/pastes", tags=["pastes"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("10/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={**auth_responses},
)
async def create_paste(
    create_request: PasteIn,
    anon_usage_service: anon_usage_service_dep,
    paste_service: paste_service_dep,
    user: optional_user_dep,
    request: Request,
):
    if user is None:
        await anon_usage_service.validate_paste_usage(request.client.host)

    create_request = create_request.model_dump()
    password = create_request.pop("password", None)

    paste = await paste_service.create_paste(
        owner_id=user.id if user else None, password=password.get_secret_value() if password else None, **create_request
    )

    return {"data": paste}


@router.get(
    "/{paste_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("10/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        **auth_responses,
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
    },
)
async def retrieve_paste(paste_id: uuid.UUID, paste_service: paste_service_dep, user: optional_user_dep):
    paste = await paste_service.get_authorized_paste_by_id(paste_id, user.id if user else None)
    return {"data": paste}
