"""Foundry-style error envelope and exception mapping."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class FoundryError(Exception):
    """Raised to produce a Foundry-compliant error response."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        error_name: str,
        parameters: dict[str, Any] | None = None,
        error_instance_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.error_name = error_name
        self.parameters = parameters or {}
        self.error_instance_id = error_instance_id
        super().__init__(error_name)

    def to_body(self, instance_id: str) -> dict[str, Any]:
        return {
            "errorCode": self.error_code,
            "errorName": self.error_name,
            "errorInstanceId": instance_id,
            "parameters": self.parameters,
        }


def next_error_instance_id(seed: int | None, counter: int) -> str:
    """Deterministic errorInstanceId from seed + counter."""
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"semblance-foundry:error:{seed}:{counter}",
        )
    )


def foundry_error_body(
    *,
    error_code: str,
    error_name: str,
    error_instance_id: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "errorCode": error_code,
        "errorName": error_name,
        "errorInstanceId": error_instance_id,
        "parameters": parameters or {},
    }


def register_exception_handlers(app: Any, seed: int | None) -> None:
    """Attach Foundry JSON error handlers to a FastAPI app."""

    counter = {"n": 0}

    def _instance_id() -> str:
        counter["n"] += 1
        return next_error_instance_id(seed, counter["n"])

    @app.exception_handler(FoundryError)
    async def foundry_error_handler(
        request: Request, exc: FoundryError
    ) -> JSONResponse:
        instance_id = exc.error_instance_id or _instance_id()
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_body(instance_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=foundry_error_body(
                error_code="INVALID_ARGUMENT",
                error_name="InvalidArgument",
                error_instance_id=_instance_id(),
                parameters={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content=foundry_error_body(
                    error_code="NOT_FOUND",
                    error_name="NotFound",
                    error_instance_id=_instance_id(),
                    parameters={"path": str(request.url.path)},
                ),
            )
        if exc.status_code == 405:
            return JSONResponse(
                status_code=405,
                content=foundry_error_body(
                    error_code="INVALID_ARGUMENT",
                    error_name="MethodNotAllowed",
                    error_instance_id=_instance_id(),
                    parameters={"path": str(request.url.path)},
                ),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=foundry_error_body(
                error_code="UNKNOWN",
                error_name="HttpException",
                error_instance_id=_instance_id(),
                parameters={},
            ),
        )
