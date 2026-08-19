"""Request helpers."""

from __future__ import annotations

from typing import Protocol, cast

from fastapi import Request

from semblance_databricks.config import DatabricksMockConfig
from semblance_databricks.errors import DatabricksError
from semblance_databricks.ids import PageTokenCodec
from semblance_databricks.state import DatabricksState


class DatabricksMockLike(Protocol):
    config: DatabricksMockConfig
    state: DatabricksState
    page_token_codec: PageTokenCodec

    def tick(self) -> None: ...


def mock_from(request: Request) -> DatabricksMockLike:
    return cast(DatabricksMockLike, request.app.state.databricks_mock)


def require_fail_stage(request: Request, stage: str) -> None:
    mock = mock_from(request)
    if mock.config.fail_stage == stage:
        raise DatabricksError(500, "INTERNAL_ERROR", f"fail_stage={stage}")


def stub_unimplemented(request: Request, name: str) -> None:
    mock = mock_from(request)
    if mock.config.auth == "strict":
        raise DatabricksError(501, "FEATURE_DISABLED", f"{name} is not implemented")
    raise DatabricksError(404, "RESOURCE_DOES_NOT_EXIST", f"{name} not found")
