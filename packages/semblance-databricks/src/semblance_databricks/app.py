"""DatabricksMock factory and ASGI construction."""

from __future__ import annotations

import random
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from semblance_databricks.auth import DatabricksMiddleware
from semblance_databricks.compatibility import manifest_json
from semblance_databricks.config import DatabricksMockConfig
from semblance_databricks.errors import register_exception_handlers
from semblance_databricks.fixtures.loaders import (
    apply_fixture,
    bundled_acme_path,
    load_fixture_file,
)
from semblance_databricks.ids import PageTokenCodec, token_secret
from semblance_databricks.services.clusters import create_clusters_router
from semblance_databricks.services.dbfs import create_dbfs_router
from semblance_databricks.services.dbsql import create_dbsql_router
from semblance_databricks.services.jobs import create_jobs_router
from semblance_databricks.services.permissions import create_permissions_router
from semblance_databricks.services.secrets import create_secrets_router
from semblance_databricks.services.workspace import create_workspace_router
from semblance_databricks.state import DatabricksState

_BUNDLED_FIXTURES = {"acme": bundled_acme_path}


def _distribution_version() -> str:
    try:
        return pkg_version("semblance-databricks")
    except PackageNotFoundError:
        return "0.1.0"


class DatabricksMock:
    """Fixture-backed local simulation of selected Databricks REST operations."""

    def __init__(self, config: DatabricksMockConfig | None = None) -> None:
        self.config = config or DatabricksMockConfig()
        self.state = DatabricksState(seed=self.config.seed)
        self.page_token_codec = PageTokenCodec(token_secret(self.config.seed))
        self._rng = random.Random(self.config.seed)

    def load_fixture(self, path: str | Path) -> DatabricksMock:
        self.state.clear()
        doc = load_fixture_file(path)
        apply_fixture(doc, self.state)
        return self

    def load_bundled_fixture(self, name: str = "acme") -> DatabricksMock:
        """Load a fixture shipped with the package (currently ``acme``)."""
        loader = _BUNDLED_FIXTURES.get(name)
        if loader is None:
            known = ", ".join(sorted(_BUNDLED_FIXTURES))
            raise ValueError(
                f"unknown bundled fixture {name!r}; expected one of: {known}"
            )
        return self.load_fixture(loader())

    def tick(self) -> None:
        """Advance virtual-clock cluster and run state machines."""
        self.state.tick()

    def register_statement(self, key: str, fn: Callable[..., Any]) -> None:
        """Register an allow-listed callback keyed by SQL text or warehouse id."""
        self.state.statement_callbacks[key] = fn

    def as_fastapi(self) -> FastAPI:
        app = FastAPI(
            title="semblance-databricks",
            description=(
                "Unofficial local simulation of selected Databricks workspace "
                "REST operations. Not affiliated with Databricks."
            ),
            version=_distribution_version(),
        )
        app.state.databricks_mock = self
        register_exception_handlers(app)
        app.add_middleware(
            DatabricksMiddleware,
            config=self.config,
            rng=self._rng,
        )
        app.include_router(create_clusters_router())
        app.include_router(create_jobs_router())
        app.include_router(create_workspace_router())
        app.include_router(create_dbsql_router())
        app.include_router(create_secrets_router())
        app.include_router(create_dbfs_router())
        app.include_router(create_permissions_router())

        @app.get("/.well-known/semblance-databricks-compat.json")
        def compatibility() -> dict[str, Any]:
            return manifest_json()

        return app
