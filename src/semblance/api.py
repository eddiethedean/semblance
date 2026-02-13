"""
Endpoint registration and FastAPI app creation.

SemblanceAPI collects GET and POST routes with input/output models and exports
a FastAPI application. Input models validate requests (query params, body, path);
output models define response shapes. Endpoint handlers are optional—Semblance
generates responses from schemas and link metadata.
"""

import asyncio
import random
import re
from collections.abc import Callable
from typing import Annotated, Any, get_origin

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from semblance.factory import build_response
from semblance.state import StatefulStore


def _parse_path_params(path: str) -> list[str]:
    """Extract path param names from template, e.g. '/users/{id}' -> ['id']."""
    return re.findall(r"\{(\w+)\}", path)


class EndpointSpec:
    """Stored spec for a single endpoint."""

    __slots__ = (
        "path",
        "methods",
        "input_model",
        "output_annotation",
        "handler",
        "list_count",
        "seed_from",
        "error_rate",
        "error_codes",
        "latency_ms",
        "jitter_ms",
        "filter_by",
        "summary",
        "description",
        "tags",
    )

    def __init__(
        self,
        path: str,
        methods: list[str],
        input_model: type[BaseModel],
        output_annotation: type,
        handler: Callable[..., Any],
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ):
        self.path = path
        self.methods = methods
        self.input_model = input_model
        self.output_annotation = output_annotation
        self.handler = handler
        self.list_count = list_count
        self.seed_from = seed_from
        self.error_rate = error_rate
        self.error_codes = error_codes or [404, 500]
        self.latency_ms = latency_ms
        self.jitter_ms = jitter_ms
        self.filter_by = filter_by
        self.summary = summary
        self.description = description
        self.tags = tags


class SemblanceAPI:
    """
    Core API builder. Register endpoints with input/output models;
    endpoint bodies are optional and ignored.

    Args:
        seed: Optional seed for deterministic random generation.
        stateful: If True, POST responses are stored and GET list endpoints
            return stored instances instead of generating new ones.
    """

    def __init__(self, seed: int | None = None, stateful: bool = False) -> None:
        self._specs: list[EndpointSpec] = []
        self._seed = seed
        self._store: StatefulStore | None = StatefulStore() if stateful else None

    def clear_store(self, path: str | None = None) -> None:
        """Clear the stateful store. Only available when stateful=True."""
        if self._store is not None:
            self._store.clear(path)

    def get(
        self,
        path: str,
        *,
        input: type[BaseModel],
        output: type,
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a GET endpoint. Query parameters are validated against `input`.
        Response is generated from `output` (single model or list[model]).

        Usage:
            @api.get("/users", input=UserQuery, output=list[User])
            def users():
                pass
        """
        return self._register(
            path,
            "GET",
            input,
            output,
            list_count,
            seed_from,
            error_rate,
            error_codes,
            latency_ms,
            jitter_ms,
            filter_by,
            summary,
            description,
            tags,
        )

    def post(
        self,
        path: str,
        *,
        input: type[BaseModel],
        output: type,
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a POST endpoint. Request body is validated against `input`.
        Response is generated from `output` (single model or list[model]).

        Usage:
            @api.post("/users", input=CreateUserRequest, output=User)
            def create_user():
                pass
        """
        return self._register(
            path,
            "POST",
            input,
            output,
            list_count,
            seed_from,
            error_rate,
            error_codes,
            latency_ms,
            jitter_ms,
            filter_by,
            summary,
            description,
            tags,
        )

    def _register(
        self,
        path: str,
        method: str,
        input_model: type[BaseModel],
        output: type,
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._specs.append(
                EndpointSpec(
                    path=path,
                    methods=[method],
                    input_model=input_model,
                    output_annotation=output,
                    handler=func,
                    list_count=list_count,
                    seed_from=seed_from,
                    error_rate=error_rate,
                    error_codes=error_codes,
                    latency_ms=latency_ms,
                    jitter_ms=jitter_ms,
                    filter_by=filter_by,
                    summary=summary,
                    description=description,
                    tags=tags,
                )
            )
            return func

        return decorator

    def as_fastapi(self) -> FastAPI:
        """Build and return a FastAPI application with all registered endpoints."""
        app = FastAPI()
        seen: set[tuple[str, str]] = set()

        for spec in self._specs:
            for method in spec.methods:
                key = (spec.path, method)
                if key in seen:
                    raise ValueError(
                        f"Duplicate {method} endpoint registered for path {spec.path!r}"
                    )
                seen.add(key)
                if method == "GET":
                    self._register_get(app, spec)
                elif method == "POST":
                    self._register_post(app, spec)

        return app

    def _resolve_seed(
        self, seed_from: str | None, input_instance: BaseModel
    ) -> int | None:
        """Resolve seed from API default or input field."""
        if self._seed is not None:
            return self._seed
        if seed_from:
            val = input_instance.model_dump().get(seed_from)
            if val is not None:
                try:
                    return int(val)
                except (TypeError, ValueError):
                    pass
        return None

    async def _await_latency(self, latency_ms: float, jitter_ms: float) -> None:
        """Await latency simulation. Call from async handler."""
        if latency_ms <= 0 and jitter_ms <= 0:
            return
        base_s = latency_ms / 1000
        jitter_s = random.uniform(-jitter_ms, jitter_ms) / 1000
        duration = max(0, base_s + jitter_s)
        if duration > 0:
            await asyncio.sleep(duration)

    def _maybe_raise_error(
        self, error_rate: float, error_codes: list[int], seed: int | None
    ) -> None:
        """With probability error_rate, raise HTTPException."""
        if error_rate <= 0:
            return
        rng = random.Random(seed) if seed is not None else random
        if rng.random() < error_rate:
            code = rng.choice(error_codes)
            raise HTTPException(status_code=code, detail="Simulated error")

    def _resolve_list_count(
        self, list_count: int | str, input_instance: BaseModel
    ) -> int:
        """Resolve list_count to int; when str, use input field value."""
        if isinstance(list_count, int):
            return max(1, list_count)
        val = input_instance.model_dump().get(list_count, 5)
        try:
            n = int(val) if val is not None else 5
            return max(1, n)
        except (TypeError, ValueError):
            return 5

    def _merge_path_params(
        self, input_model: type[BaseModel], data: BaseModel, path_params: dict[str, Any]
    ) -> BaseModel:
        """Merge path params into validated input for build_response."""
        if not path_params:
            return data
        merged = {**data.model_dump(), **path_params}
        return input_model.model_validate(merged)

    def _register_get(self, app: FastAPI, spec: EndpointSpec) -> None:
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        filter_by = spec.filter_by
        path_params = _parse_path_params(spec.path)
        store = self._store
        path = spec.path

        if path_params:

            async def handler(
                request: Request,
                query: Annotated[input_model, Query()],  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                merged = self._merge_path_params(
                    input_model, query, dict(request.path_params)
                )
                seed = self._resolve_seed(seed_from, merged)
                self._maybe_raise_error(error_rate, error_codes, seed)
                await self._await_latency(latency_ms, jitter_ms)
                if store is not None and get_origin(output_annotation) is list:
                    return store.get_all(path)
                count = self._resolve_list_count(list_count, merged)
                return build_response(
                    output_annotation,
                    input_model,
                    merged,
                    list_count=count,
                    seed=seed,
                    filter_by=filter_by,
                )

        else:

            async def handler(
                query: Annotated[input_model, Query()],  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                seed = self._resolve_seed(seed_from, query)
                self._maybe_raise_error(error_rate, error_codes, seed)
                await self._await_latency(latency_ms, jitter_ms)
                if store is not None and get_origin(output_annotation) is list:
                    return store.get_all(path)
                count = self._resolve_list_count(list_count, query)
                return build_response(
                    output_annotation,
                    input_model,
                    query,
                    list_count=count,
                    seed=seed,
                    filter_by=filter_by,
                )

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.get(spec.path, **kwargs)(handler)

    def _register_post(self, app: FastAPI, spec: EndpointSpec) -> None:
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        filter_by = spec.filter_by
        path_params = _parse_path_params(spec.path)
        store = self._store
        path = spec.path

        if path_params:

            async def handler(
                request: Request,
                body: input_model,  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                merged = self._merge_path_params(
                    input_model, body, dict(request.path_params)
                )
                seed = self._resolve_seed(seed_from, merged)
                self._maybe_raise_error(error_rate, error_codes, seed)
                await self._await_latency(latency_ms, jitter_ms)
                count = self._resolve_list_count(list_count, merged)
                response = build_response(
                    output_annotation,
                    input_model,
                    merged,
                    list_count=count,
                    seed=seed,
                    filter_by=filter_by,
                )
                if store is not None and not isinstance(response, list):
                    response = store.add(path, response)
                return response

        else:

            async def handler(
                body: input_model,  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                seed = self._resolve_seed(seed_from, body)
                self._maybe_raise_error(error_rate, error_codes, seed)
                await self._await_latency(latency_ms, jitter_ms)
                count = self._resolve_list_count(list_count, body)
                response = build_response(
                    output_annotation,
                    input_model,
                    body,
                    list_count=count,
                    seed=seed,
                    filter_by=filter_by,
                )
                if store is not None and not isinstance(response, list):
                    response = store.add(path, response)
                return response

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.post(spec.path, **kwargs)(handler)
