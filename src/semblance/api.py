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

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel

from semblance.config import load_config
from semblance.factory import build_response, validate_response
from semblance.rate_limit import get_limiter
from semblance.state import StatefulStore
from semblance.validation import validate_specs


def _parse_path_params(path: str) -> list[str]:
    """Extract path param names from template, e.g. '/users/{id}' -> ['id']."""
    return re.findall(r"\{(\w+)\}", path)


def _collection_path(path_template: str) -> str:
    """Strip the last /{param} segment for store key. '/users/{id}' -> '/users'."""
    return re.sub(r"/\{\w+\}$", "", path_template)


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
        "rate_limit",
        "summary",
        "description",
        "tags",
    )

    def __init__(
        self,
        path: str,
        methods: list[str],
        input_model: type[BaseModel],
        output_annotation: type | None,
        handler: Callable[..., Any],
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        rate_limit: float | None = None,
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
        self.rate_limit = rate_limit
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
        validate_responses: If True, generated responses are validated against
            the output model (for development/CI; adds overhead).
        validate_links: If True, at as_fastapi() validate that link bindings
            (FromInput, DateRangeFrom, etc.) reference existing input/output
            fields; raise ValueError with details if not. Default False for
            backward compatibility.
        verbose_errors: If True, stateful 404 responses include collection path
            and id field/value in the detail for easier debugging.
    """

    def __init__(
        self,
        seed: int | None = None,
        stateful: bool = False,
        validate_responses: bool = False,
        validate_links: bool = False,
        verbose_errors: bool = False,
        config_path: str | None = None,
    ) -> None:
        self._specs: list[EndpointSpec] = []
        cfg = load_config(config_path) if config_path is not None else None
        self._seed = seed if seed is not None else (cfg.seed if cfg else None)
        _stateful = stateful or (cfg.stateful if cfg else False)
        self._store = StatefulStore() if _stateful else None
        self._validate_responses = validate_responses or (
            cfg.validate_responses if cfg else False
        )
        self._validate_links = validate_links or (
            getattr(cfg, "validate_links", False) if cfg else False
        )
        self._verbose_errors = verbose_errors or (
            getattr(cfg, "verbose_errors", False) if cfg else False
        )
        self._middleware: list[tuple[type[Any], dict[str, Any]]] = []

    @classmethod
    def from_config(
        cls,
        config_path: str | None = None,
        **kwargs: Any,
    ) -> "SemblanceAPI":
        """Build a SemblanceAPI with defaults from config. Keyword args override config."""
        cfg = load_config(config_path)
        return cls(
            seed=kwargs.pop("seed", cfg.seed),
            stateful=kwargs.pop("stateful", cfg.stateful),
            validate_responses=kwargs.pop("validate_responses", cfg.validate_responses),
            validate_links=kwargs.pop("validate_links", getattr(cfg, "validate_links", False)),
            verbose_errors=kwargs.pop("verbose_errors", getattr(cfg, "verbose_errors", False)),
            **kwargs,
        )

    def get_endpoint_specs(self) -> list[EndpointSpec]:
        """Return a copy of the registered endpoint specs (for plugins/tooling)."""
        return list(self._specs)

    def get_spec(self, path: str, method: str) -> EndpointSpec | None:
        """Return the endpoint spec for (path, method), or None if not found."""
        for spec in self._specs:
            if spec.path == path and method.upper() in spec.methods:
                return spec
        return None

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
        rate_limit: float | None = None,
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
            rate_limit,
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
        rate_limit: float | None = None,
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
            rate_limit,
            summary,
            description,
            tags,
        )

    def put(
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
        rate_limit: float | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a PUT endpoint. Request body is validated against `input`.
        Response is generated from `output` (single model or list[model]).

        Usage:
            @api.put("/users/{id}", input=UpdateUserRequest, output=User)
            def update_user():
                pass
        """
        return self._register(
            path,
            "PUT",
            input,
            output,
            list_count,
            seed_from,
            error_rate,
            error_codes,
            latency_ms,
            jitter_ms,
            filter_by,
            rate_limit,
            summary,
            description,
            tags,
        )

    def patch(
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
        rate_limit: float | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a PATCH endpoint. Request body is validated against `input`.
        Response is generated from `output` (single model or list[model]).

        Usage:
            @api.patch("/users/{id}", input=PatchUserRequest, output=User)
            def patch_user():
                pass
        """
        return self._register(
            path,
            "PATCH",
            input,
            output,
            list_count,
            seed_from,
            error_rate,
            error_codes,
            latency_ms,
            jitter_ms,
            filter_by,
            rate_limit,
            summary,
            description,
            tags,
        )

    def delete(
        self,
        path: str,
        *,
        input: type[BaseModel],
        output: type | None = None,
        rate_limit: float | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a DELETE endpoint. Path params (and optional body) are validated
        against `input`. If `output` is None, returns 204 No Content.
        If `output` is a model, returns 200 with generated body.

        Usage:
            @api.delete("/users/{id}", input=DeleteUserQuery)
            def delete_user():
                pass
        """
        return self._register(
            path,
            "DELETE",
            input,
            output,
            list_count=1,
            seed_from=None,
            error_rate=0,
            error_codes=None,
            latency_ms=0,
            jitter_ms=0,
            filter_by=None,
            rate_limit=rate_limit,
            summary=summary,
            description=description,
            tags=tags,
        )

    def _register(
        self,
        path: str,
        method: str,
        input_model: type[BaseModel],
        output: type | None,
        list_count: int | str = 5,
        seed_from: str | None = None,
        error_rate: float = 0,
        error_codes: list[int] | None = None,
        latency_ms: float = 0,
        jitter_ms: float = 0,
        filter_by: str | None = None,
        rate_limit: float | None = None,
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
                    rate_limit=rate_limit,
                    summary=summary,
                    description=description,
                    tags=tags,
                )
            )
            return func

        return decorator

    def add_middleware(self, middleware_class: type[Any], **kwargs: Any) -> None:
        """Register a FastAPI/Starlette middleware. First added is outermost."""
        self._middleware.append((middleware_class, kwargs))

    def mount_into(self, app: FastAPI, path_prefix: str = "/") -> None:
        """Mount this Semblance API at path_prefix on an existing FastAPI app."""
        sub_app = self.as_fastapi()
        prefix = path_prefix.rstrip("/") or "/"
        app.mount(prefix, sub_app)

    def as_fastapi(self) -> FastAPI:
        """Build and return a FastAPI application with all registered endpoints."""
        if self._validate_links:
            link_errors = validate_specs(self._specs)
            if link_errors:
                raise ValueError("Link validation failed:\n" + "\n".join(link_errors))
        app = FastAPI()
        for mw_class, mw_kwargs in self._middleware:
            app.add_middleware(mw_class, **mw_kwargs)  # type: ignore[arg-type]
        seen: set[tuple[str, str]] = set()

        for spec in self._specs:
            for method in spec.methods:
                key = (spec.path, method)
                if key in seen:
                    raise ValueError(
                        f"Duplicate {method} endpoint registered for path {spec.path!r}. "
                        "Register only one handler per (path, method)."
                    )
                seen.add(key)
                if method == "GET":
                    self._register_get(app, spec)
                elif method == "POST":
                    self._register_post(app, spec)
                elif method == "PUT":
                    self._register_put(app, spec)
                elif method == "PATCH":
                    self._register_patch(app, spec)
                elif method == "DELETE":
                    self._register_delete(app, spec)

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

    def _check_rate_limit(self, spec: EndpointSpec) -> None:
        """Raise HTTPException 429 if rate limit exceeded."""
        if spec.rate_limit is None or spec.rate_limit <= 0:
            return
        limiter = get_limiter()
        method = spec.methods[0]
        if not limiter.check_and_record(spec.path, method, spec.rate_limit):
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded (simulated)"
            )

    def _openapi_responses(self, spec: EndpointSpec) -> dict[int, dict[str, str]]:
        """Build OpenAPI response descriptions for rate limit and simulated errors."""
        responses: dict[int, dict[str, str]] = {}
        if spec.rate_limit is not None and spec.rate_limit > 0:
            responses[429] = {"description": "Rate limit exceeded (simulated)"}
        if spec.error_rate and spec.error_rate > 0 and spec.error_codes:
            for code in spec.error_codes:
                responses[code] = {"description": "Simulated error"}
        return responses

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
        store = self._store
        path = spec.path

        async def handler(
            request: Request,
            query: Annotated[input_model, Query()],
        ) -> output_annotation:
            assert output_annotation is not None
            self._check_rate_limit(spec)
            merged = self._merge_path_params(
                input_model, query, dict(request.path_params)
            )
            seed = self._resolve_seed(seed_from, merged)
            self._maybe_raise_error(error_rate, error_codes, seed)
            await self._await_latency(latency_ms, jitter_ms)
            response: BaseModel | list[BaseModel]
            if store is not None and get_origin(output_annotation) is list:
                response = store.get_all(path)
                if self._validate_responses:
                    validate_response(output_annotation, response)
                return response
            if store is not None and get_origin(output_annotation) is not list:
                path_param_names = _parse_path_params(path)
                if path_param_names:
                    path_params = dict(request.path_params)
                    collection_path = _collection_path(path)
                    id_field = path_param_names[0]
                    id_value = path_params.get(id_field)
                    if id_value is not None:
                        item = store.get_by_id(collection_path, id_value, id_field)
                        if item is not None:
                            if self._validate_responses:
                                validate_response(output_annotation, item)
                            return item
                        detail: str | dict[str, Any] = "Not found"
                        if self._verbose_errors:
                            detail = {
                                "detail": "Not found",
                                "collection": collection_path,
                                "id_field": id_field,
                                "id_value": id_value,
                            }
                        raise HTTPException(status_code=404, detail=detail)
            count = self._resolve_list_count(list_count, merged)
            response = build_response(
                output_annotation,
                input_model,
                merged,
                list_count=count,
                seed=seed,
                filter_by=filter_by,
                request=request,
            )
            if self._validate_responses:
                validate_response(output_annotation, response)
            return response

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        extra = self._openapi_responses(spec)
        if extra:
            kwargs["responses"] = extra
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.get(spec.path, **kwargs)(handler)

    def _register_post(self, app: FastAPI, spec: EndpointSpec) -> None:
        assert spec.output_annotation is not None
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        filter_by = spec.filter_by
        store = self._store
        path = spec.path

        async def handler(
            request: Request,
            body: input_model,
        ) -> output_annotation:
            self._check_rate_limit(spec)
            merged = self._merge_path_params(
                input_model, body, dict(request.path_params)
            )
            seed = self._resolve_seed(seed_from, merged)
            self._maybe_raise_error(error_rate, error_codes, seed)
            await self._await_latency(latency_ms, jitter_ms)
            count = self._resolve_list_count(list_count, merged)
            response: BaseModel | list[BaseModel] = build_response(
                output_annotation,
                input_model,
                merged,
                list_count=count,
                seed=seed,
                filter_by=filter_by,
                request=request,
            )
            if store is not None and not isinstance(response, list):
                response = store.add(path, response)
            if self._validate_responses:
                validate_response(output_annotation, response)
            return response

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        extra = self._openapi_responses(spec)
        if extra:
            kwargs["responses"] = extra
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.post(spec.path, **kwargs)(handler)

    def _register_put(self, app: FastAPI, spec: EndpointSpec) -> None:
        assert spec.output_annotation is not None
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        filter_by = spec.filter_by
        store = self._store
        path = spec.path

        async def handler(
            request: Request,
            body: input_model,
        ) -> output_annotation:
            self._check_rate_limit(spec)
            merged = self._merge_path_params(
                input_model, body, dict(request.path_params)
            )
            seed = self._resolve_seed(seed_from, merged)
            self._maybe_raise_error(error_rate, error_codes, seed)
            await self._await_latency(latency_ms, jitter_ms)
            count = self._resolve_list_count(list_count, merged)
            response: BaseModel | list[BaseModel] = build_response(
                output_annotation,
                input_model,
                merged,
                list_count=count,
                seed=seed,
                filter_by=filter_by,
                request=request,
            )
            if store is not None:
                path_param_names = _parse_path_params(path)
                if path_param_names:
                    path_params = dict(request.path_params)
                    collection_path = _collection_path(path)
                    id_field = path_param_names[0]
                    id_value = path_params.get(id_field)
                    if id_value is not None:
                        if not isinstance(response, BaseModel):
                            raise TypeError("PUT response must be a single model")
                        resp: BaseModel = response
                        if (
                            "id" in type(resp).model_fields
                            or id_field in type(resp).model_fields
                        ):
                            data = resp.model_dump()
                            data[id_field] = id_value
                            resp = type(resp).model_validate(data)
                        existing = store.get_by_id(collection_path, id_value, id_field)
                        if existing is not None:
                            resp = (
                                store.update(
                                    collection_path,
                                    id_value,
                                    resp,
                                    id_field,
                                )
                                or resp
                            )
                        else:
                            resp = store.add(collection_path, resp)
                        response = resp
            if self._validate_responses:
                validate_response(output_annotation, response)
            return response

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        extra = self._openapi_responses(spec)
        if extra:
            kwargs["responses"] = extra
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.put(spec.path, **kwargs)(handler)

    def _register_patch(self, app: FastAPI, spec: EndpointSpec) -> None:
        assert spec.output_annotation is not None
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        filter_by = spec.filter_by
        store = self._store
        path = spec.path

        async def handler(
            request: Request,
            body: input_model,
        ) -> output_annotation:
            self._check_rate_limit(spec)
            merged = self._merge_path_params(
                input_model, body, dict(request.path_params)
            )
            seed = self._resolve_seed(seed_from, merged)
            self._maybe_raise_error(error_rate, error_codes, seed)
            await self._await_latency(latency_ms, jitter_ms)
            if store is not None:
                path_param_names = _parse_path_params(path)
                if path_param_names:
                    path_params = dict(request.path_params)
                    collection_path = _collection_path(path)
                    id_field = path_param_names[0]
                    id_value = path_params.get(id_field)
                    if id_value is not None:
                        existing = store.get_by_id(collection_path, id_value, id_field)
                        if existing is None:
                            detail_patch: str | dict[str, Any] = "Not found"
                            if self._verbose_errors:
                                detail_patch = {
                                    "detail": "Not found",
                                    "collection": collection_path,
                                    "id_field": id_field,
                                    "id_value": id_value,
                                }
                            raise HTTPException(status_code=404, detail=detail_patch)
            count = self._resolve_list_count(list_count, merged)
            response: BaseModel | list[BaseModel] = build_response(
                output_annotation,
                input_model,
                merged,
                list_count=count,
                seed=seed,
                filter_by=filter_by,
                request=request,
            )
            if store is not None:
                path_param_names = _parse_path_params(path)
                if path_param_names:
                    path_params = dict(request.path_params)
                    collection_path = _collection_path(path)
                    id_field = path_param_names[0]
                    id_value = path_params.get(id_field)
                    if id_value is not None:
                        if not isinstance(response, BaseModel):
                            raise TypeError("PATCH response must be a single model")
                        resp: BaseModel = response
                        if id_field in type(resp).model_fields:
                            data = resp.model_dump()
                            data[id_field] = id_value
                            resp = type(resp).model_validate(data)
                        updated = store.update(
                            collection_path,
                            id_value,
                            resp,
                            id_field,
                        )
                        if updated is not None:
                            response = updated
                        else:
                            response = resp
            if self._validate_responses:
                validate_response(output_annotation, response)
            return response

        kwargs: dict[str, Any] = {"response_model": output_annotation}
        extra = self._openapi_responses(spec)
        if extra:
            kwargs["responses"] = extra
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.patch(spec.path, **kwargs)(handler)

    def _register_delete(self, app: FastAPI, spec: EndpointSpec) -> None:
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        seed_from = spec.seed_from
        error_rate = spec.error_rate
        error_codes = spec.error_codes
        latency_ms = spec.latency_ms
        jitter_ms = spec.jitter_ms
        store = self._store
        path = spec.path

        async def handler(
            request: Request,
            body: input_model | None = Body(None),
        ) -> Any:
            self._check_rate_limit(spec)
            path_params = dict(request.path_params)
            data: dict[str, Any] = body.model_dump() if body is not None else {}
            merged = input_model.model_validate({**data, **path_params})
            seed = self._resolve_seed(seed_from, merged)
            self._maybe_raise_error(error_rate, error_codes, seed)
            await self._await_latency(latency_ms, jitter_ms)
            if store is not None:
                path_param_names = _parse_path_params(path)
                if path_param_names:
                    id_field = path_param_names[0]
                    id_value = path_params.get(id_field)
                    if id_value is not None:
                        collection_path = _collection_path(path)
                        if not store.remove(collection_path, id_value, id_field):
                            detail_del: str | dict[str, Any] = "Not found"
                            if self._verbose_errors:
                                detail_del = {
                                    "detail": "Not found",
                                    "collection": collection_path,
                                    "id_field": id_field,
                                    "id_value": id_value,
                                }
                            raise HTTPException(status_code=404, detail=detail_del)
                        return Response(status_code=204)
            if output_annotation is None:
                return Response(status_code=204)
            response: BaseModel | list[BaseModel] = build_response(
                output_annotation,
                input_model,
                merged,
                list_count=1,
                seed=seed,
                filter_by=None,
                request=request,
            )
            if self._validate_responses:
                validate_response(output_annotation, response)
            return response

        kwargs: dict[str, Any] = {}
        if output_annotation is not None:
            kwargs["response_model"] = output_annotation
        extra = self._openapi_responses(spec)
        if extra:
            kwargs["responses"] = extra
        if spec.summary is not None:
            kwargs["summary"] = spec.summary
        if spec.description is not None:
            kwargs["description"] = spec.description
        if spec.tags is not None:
            kwargs["tags"] = spec.tags
        app.delete(spec.path, **kwargs)(handler)
