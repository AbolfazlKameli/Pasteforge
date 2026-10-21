from typing import TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class DataSchema[DataT](BaseModel):
    data: DataT


class HealthCheckResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error: str


class SuccessResponse(BaseModel):
    message: str
