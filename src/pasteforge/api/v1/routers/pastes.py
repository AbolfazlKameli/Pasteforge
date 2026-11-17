import uuid

from fastapi import APIRouter, Depends, Request, status
from redis_fastapi import rate_limit

from pasteforge.api.dependencies import (
    active_user_dep,
    anon_usage_service_dep,
    idempotency_key_dep,
    idempotency_service_dep,
    optional_user_dep,
    paste_service_dep,
)
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
        idempotency_key: idempotency_key_dep,
        idempotency_service: idempotency_service_dep,
):
    create_data = create_request.model_dump(exclude={"password"})
    password = _get_password_hash_input(create_request.password)

    user_id = user.id if user else None

    idempotency_scope = idempotency_service.build_scope_key(user_id, request.client.host)
    request_hash = idempotency_service.generate_request_hash(
        method=request.method, path=request.url.path, payload=create_request
    )

    idempotency_response, record_id = await idempotency_service.claim_idempotency(
        scope_key=idempotency_scope, idempotency_key=idempotency_key, request_hash=request_hash
    )

    if idempotency_response is not None:
        return {"data": PasteOut.model_validate_json(idempotency_response)}

    if user is None:
        await anon_usage_service.validate_paste_usage(request.client.host)

    paste = await paste_service.create_paste(owner_id=user_id, password=password, **create_data)

    await idempotency_service.complete_idempotency(
        record_id=record_id,
        response_status=status.HTTP_201_CREATED,
        response_body=PasteOut.model_validate(paste).model_dump_json(),
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


@router.patch(
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
    update_data = update_request.model_dump(exclude={"password", "new_password"}, exclude_unset=True)

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
