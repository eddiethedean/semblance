"""
Endpoint registration and FastAPI app creation.

SemblanceAPI collects GET (and later POST) routes with input/output models
and exports a FastAPI application that validates input and generates responses.
"""

from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from fastapi import FastAPI, Query
from pydantic import BaseModel

from semblance.factory import build_response

T = TypeVar("T", bound=BaseModel)


class EndpointSpec:
    """Stored spec for a single endpoint."""

    __slots__ = ("path", "methods", "input_model", "output_annotation", "handler", "list_count")

    def __init__(
        self,
        path: str,
        methods: list[str],
        input_model: type[BaseModel],
        output_annotation: type,
        handler: Callable[..., Any],
        list_count: int = 5,
    ):
        self.path = path
        self.methods = methods
        self.input_model = input_model
        self.output_annotation = output_annotation
        self.handler = handler
        self.list_count = list_count


class SemblanceAPI:
    """
    Core API builder. Register endpoints with input/output models;
    endpoint bodies are optional and ignored.
    """

    def __init__(self) -> None:
        self._specs: list[EndpointSpec] = []

    def get(
        self,
        path: str,
        *,
        input: type[BaseModel],
        output: type,
        list_count: int = 5,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a GET endpoint. Query parameters are validated against `input`.
        Response is generated from `output` (single model or list[model]).

        Usage:
            @api.get("/users", input=UserQuery, output=list[User])
            def users():
                pass
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._specs.append(
                EndpointSpec(
                    path=path,
                    methods=["GET"],
                    input_model=input,
                    output_annotation=output,
                    handler=func,
                    list_count=list_count,
                )
            )
            return func

        return decorator

    def as_fastapi(self) -> FastAPI:
        """Build and return a FastAPI application with all registered endpoints."""
        app = FastAPI()

        for spec in self._specs:
            if "GET" in spec.methods:
                self._register_get(app, spec)

        return app

    def _register_get(self, app: FastAPI, spec: EndpointSpec) -> None:
        input_model = spec.input_model
        output_annotation = spec.output_annotation
        list_count = spec.list_count

        async def handler(
            query: Annotated[input_model, Query()]  # type: ignore[valid-type]
        ) -> output_annotation:  # type: ignore[valid-type]
            return build_response(
                output_annotation,
                input_model,
                query,
                list_count=list_count,
            )

        app.get(spec.path, response_model=output_annotation)(handler)
