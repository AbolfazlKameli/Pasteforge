from enum import Enum

from pydantic import BaseModel, Field


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class MigrationStatus(Enum):
    UP_TO_DATE = "up_to_date"
    OUT_OF_SYNC = "out_of_sync"


class LivenessResponse(BaseModel):
    status: str = "alive"


class MigrationHealth(BaseModel):
    status: MigrationStatus
    current: list[str] = Field(default_factory=list)
    expected: list[str] = Field(default_factory=list)


class PostgresHealth(BaseModel):
    status: HealthStatus
    database: str
    migrations: MigrationHealth | None = None


class RedisHealth(BaseModel):
    status: HealthStatus
    connection: str
    cache: str


class CeleryHealth(BaseModel):
    status: HealthStatus
    workers: list[str] = Field(default_factory=list)
    count: int
    message: str | None = None


class HealthChecks(BaseModel):
    postgres: PostgresHealth
    redis: RedisHealth
    celery: CeleryHealth


class HealthResponse(BaseModel):
    status: HealthStatus
    checks: HealthChecks
