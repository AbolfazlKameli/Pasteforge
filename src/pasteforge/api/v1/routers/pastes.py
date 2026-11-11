import uuid

from fastapi import APIRouter, Depends, Request, status
from redis_fastapi import rate_limit

from pasteforge.api.dependencies import active_user_dep, anon_usage_service_dep, optional_user_dep, paste_service_dep
from pasteforge.core.exceptions import too_many_requests_error
from pasteforge.schemas.auth import auth_responses
from pasteforge.schemas.common import DataSchema, ErrorResponse
from pasteforge.schemas.pastes import (
    PasteDeleteRequest,
    PasteExpiryRequest,
    PasteIn,
    PasteOut,
    PasteUpdateRequest,
    ProtectedPasteRequest,
)

router = APIRouter(prefix="/pastes", tags=["pastes"])


def _get_password_hash_input(password) -> str | None:
    return password.get_secret_value() if password else None


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("10/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        **auth_responses,
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def create_paste(
    create_request: PasteIn,
    request: Request,
    paste_service: paste_service_dep,
    user: optional_user_dep,
    anon_usage_service: anon_usage_service_dep,
):
    if user is None:
        await anon_usage_service.validate_paste_usage(request.client.host)

    create_data = create_request.model_dump(exclude={"password"})
    password = _get_password_hash_input(create_request.password)

    paste = await paste_service.create_paste(owner_id=user.id if user else None, password=password, **create_data)

    return {"data": paste}


@router.get(
    "/{paste_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("10/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        **auth_responses,
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def retrieve_paste(paste_id: uuid.UUID, paste_service: paste_service_dep, user: optional_user_dep):
    paste = await paste_service.get_authorized_paste_by_id(paste_id, user.id if user else None)
    return {"data": paste}


@router.post(
    "/{paste_id}/secret",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("10/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def retrieve_password_protected_paste(
    paste_id: uuid.UUID, retrieve_request: ProtectedPasteRequest, paste_service: paste_service_dep
):
    paste = await paste_service.get_protected_paste_by_id(paste_id, retrieve_request.password.get_secret_value())
    return {"data": paste}


@router.put(
    "/{paste_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        **auth_responses,
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def update_paste(
    paste_id: uuid.UUID, update_request: PasteUpdateRequest, paste_service: paste_service_dep, user: active_user_dep
):
    update_data = update_request.model_dump(exclude={"password", "new_password"})

    paste = await paste_service.update_paste(
        paste_id,
        user.id,
        _get_password_hash_input(update_request.password),
        _get_password_hash_input(update_request.new_password),
        **update_data,
    )

    return {"data": paste}


@router.post(
    "/{paste_id}/expiration",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    response_model=DataSchema[PasteOut],
    responses={
        **auth_responses,
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def update_paste_expiration(
    paste_id: uuid.UUID, update_request: PasteExpiryRequest, paste_service: paste_service_dep, user: active_user_dep
):
    paste = await paste_service.update_manageable_paste_expiration(
        paste_id, user.id, _get_password_hash_input(update_request.password), update_request.expires_at
    )
    return {"data": paste}


@router.delete(
    "/{paste_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("5/minute", on_limit_exceeded=too_many_requests_error))],
    responses={
        **auth_responses,
        status.HTTP_404_NOT_FOUND: {"model": DataSchema[ErrorResponse], "description": "Paste not found."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": DataSchema[ErrorResponse], "description": "Too many requests."},
    },
)
async def delete_paste(
    paste_id: uuid.UUID, delete_request: PasteDeleteRequest, user: active_user_dep, paste_service: paste_service_dep
):
    await paste_service.delete_paste_by_id(paste_id, user.id, _get_password_hash_input(delete_request.password))
