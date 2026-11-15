from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from rest_framework.response import Response

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class ApiResponseDto(Generic[T]):
    data: T | None = None
    http_code: int = 200
    error_messages: list[str] = field(default_factory=list)
    success_messages: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "isSuccess": 200 <= self.http_code < 300,
            "errorMessages": list(self.error_messages),
            "successMessages": list(self.success_messages),
            "httpCode": self.http_code,
            "data": self.data,
            "meta": dict(self.meta),
        }


class ApiResponse(Response):
    """Respuesta JSON comun; httpCode coincide con el estado HTTP real."""

    def __init__(
        self,
        data=None,
        *,
        http_code=200,
        error_messages=None,
        success_messages=None,
        meta=None,
        headers=None,
    ):
        contract = ApiResponseDto(
            data=data,
            http_code=http_code,
            error_messages=error_messages or [],
            success_messages=success_messages or [],
            meta=meta or {},
        )
        super().__init__(contract.to_dict(), status=http_code, headers=headers)
