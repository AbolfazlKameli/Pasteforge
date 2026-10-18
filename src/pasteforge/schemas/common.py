from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class DataSchema(BaseModel, Generic[DataT]):
    data: DataT


class HealthCheckResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error: str


class SuccessResponse(BaseModel):
    message: str
