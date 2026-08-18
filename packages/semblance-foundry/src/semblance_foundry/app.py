"""FoundryMock factory and ASGI construction."""

from __future__ import annotations

import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from semblance_foundry.auth import FoundryMiddleware
from semblance_foundry.compatibility import manifest_json
from semblance_foundry.config import FoundryMockConfig
from semblance_foundry.errors import register_exception_handlers
from semblance_foundry.fixtures.loaders import apply_fixture, load_fixture_file
from semblance_foundry.ids import PageTokenCodec, rid_secret
from semblance_foundry.services.ontologies import create_ontology_router
from semblance_foundry.state import FoundryState, OntologyMutations


class FoundryMock:
    """Fixture-backed local simulation of selected Foundry API v2 operations."""

    def __init__(self, config: FoundryMockConfig | None = None) -> None:
        self.config = config or FoundryMockConfig()
        self.state = FoundryState(seed=self.config.seed)
        self.page_token_codec = PageTokenCodec(rid_secret(self.config.seed))
        self._rng = random.Random(self.config.seed)
        self.ontologies = OntologyMutations(self.state)

    def load_fixture(self, path: str | Path) -> FoundryMock:
        doc = load_fixture_file(path)
        apply_fixture(doc, self.state)
        return self

    def register_query(self, api_name: str, fn: Callable[..., Any]) -> None:
        """Register an allow-listed Python callback for query execute."""
        self.state.register_query(api_name, fn)

    def as_fastapi(self) -> FastAPI:
        app = FastAPI(
            title="semblance-foundry",
            description=(
                "Unofficial local simulation of selected Palantir Foundry "
                "API v2 ontology operations. Not affiliated with Palantir."
            ),
            version="0.1.0",
        )
        app.state.foundry_mock = self
        register_exception_handlers(app, self.config.seed)
        app.add_middleware(
            FoundryMiddleware,
            config=self.config,
            rng=self._rng,
            error_counter={"n": 0},
        )
        app.include_router(create_ontology_router())

        @app.get("/.well-known/foundry-mock-compatibility.json")
        def compatibility() -> dict[str, Any]:
            return manifest_json()

        return app
