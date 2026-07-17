from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
    code: int
