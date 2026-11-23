from fastapi import APIRouter, status

from pasteforge.api.dependencies import health_service_dep
from pasteforge.core.exceptions import ServiceUnavailableError
from pasteforge.schemas.common import DataSchema, DetailedErrorResponse
from pasteforge.schemas.health import HealthResponse, LivenessResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK, response_model=DataSchema[LivenessResponse])
async def liveness():
    return {"data": {"status": "alive"}}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[HealthResponse],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": DataSchema[DetailedErrorResponse[HealthResponse]],
            "description": "Error when service is not available.",
        }
    },
)
async def readiness(health_service: health_service_dep):
    is_healthy, checks = await health_service.check_health()

    if not is_healthy:
        raise ServiceUnavailableError(checks=checks)

    return {"data": {"status": "healthy" if is_healthy else "unhealthy", "checks": checks}}
