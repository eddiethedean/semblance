"""
Endpoint registration and FastAPI app creation.

SemblanceAPI collects GET (and later POST) routes with input/output models
and exports a FastAPI application that validates input and generates responses.
"""

import random
import re
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from semblance.factory import build_response


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


class SemblanceAPI:
    """
    Core API builder. Register endpoints with input/output models;
    endpoint bodies are optional and ignored.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._specs: list[EndpointSpec] = []
        self._seed = seed

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
            path, "GET", input, output, list_count, seed_from, error_rate, error_codes
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
            path, "POST", input, output, list_count, seed_from, error_rate, error_codes
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
                    raise ValueError(f"Duplicate {method} endpoint registered for path {spec.path!r}")
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
        path_params = _parse_path_params(spec.path)

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
                count = self._resolve_list_count(list_count, merged)
                return build_response(
                    output_annotation,
                    input_model,
                    merged,
                    list_count=count,
                    seed=seed,
                )

        else:

            async def handler(
                query: Annotated[input_model, Query()]  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                seed = self._resolve_seed(seed_from, query)
                self._maybe_raise_error(error_rate, error_codes, seed)
                count = self._resolve_list_count(list_count, query)
                return build_response(
                    output_annotation,
                    input_model,
                    query,
                    list_count=count,
                    seed=seed,
                )

        app.get(spec.path, response_model=output_annotation)(handler)

    def _register_post(self, app: FastAPI, spec: EndpointSpec) -> None:
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        path_params = _parse_path_params(spec.path)

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
                count = self._resolve_list_count(list_count, merged)
                return build_response(
                    output_annotation,
                    input_model,
                    merged,
                    list_count=count,
                    seed=seed,
                )

        else:

            async def handler(
                body: input_model  # type: ignore[valid-type]
            ) -> output_annotation:  # type: ignore[valid-type]
                seed = self._resolve_seed(seed_from, body)
                self._maybe_raise_error(error_rate, error_codes, seed)
                count = self._resolve_list_count(list_count, body)
                return build_response(
                    output_annotation,
                    input_model,
                    body,
                    list_count=count,
                    seed=seed,
                )

        app.post(spec.path, response_model=output_annotation)(handler)
