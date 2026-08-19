"""Databricks error_code/message mapper."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class DatabricksError(Exception):
    """Raised to produce a Databricks-style error response."""

    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)

    def to_body(self) -> dict[str, str]:
        return {"error_code": self.error_code, "message": self.message}


def databricks_error_body(error_code: str, message: str) -> dict[str, str]:
    return {"error_code": error_code, "message": message}


def register_exception_handlers(app: Any) -> None:
    @app.exception_handler(DatabricksError)
    async def databricks_error_handler(
        request: Request, exc: DatabricksError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_body())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=databricks_error_body(
                "INVALID_PARAMETER_VALUE",
                "Invalid request",
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content=databricks_error_body(
                    "RESOURCE_DOES_NOT_EXIST",
                    f"Path {request.url.path} does not exist",
                ),
            )
        if exc.status_code == 405:
            return JSONResponse(
                status_code=405,
                content=databricks_error_body(
                    "INVALID_PARAMETER_VALUE",
                    "Method not allowed",
                ),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=databricks_error_body("UNKNOWN", "HTTP error"),
        )
