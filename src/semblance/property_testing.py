"""
Property-based testing helpers for Semblance APIs.

Generate Hypothesis strategies from input models and run endpoint tests
that validate responses against output schemas and optional invariants.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Annotated, Any, Protocol, get_args, get_origin

from pydantic import BaseModel

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError as e:
    raise ImportError(
        "Property-based testing requires hypothesis. Install with: pip install semblance[dev]"
    ) from e


def _parse_path_params(path: str) -> list[str]:
    """Extract path param names from template, e.g. '/users/{id}' -> ['id']."""
    return re.findall(r"\{(\w+)\}", path)


def _get_bare_annotation(annotation: type) -> type:
    """Strip Annotated and Union to get a concrete type for strategy generation."""
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Annotated and args:
        return _get_bare_annotation(args[0])
    if origin is type(None) or (origin is not None and "Union" in str(origin)) and args:
        for a in args:
            if a is type(None):
                continue
            return _get_bare_annotation(a)
    return annotation


def _strategy_for_annotation(annotation: type) -> st.SearchStrategy[Any]:
    """Build a Hypothesis strategy for a single field annotation."""
    bare = _get_bare_annotation(annotation)
    if bare is type(None):
        return st.none()
    try:
        if isinstance(bare, type) and issubclass(bare, BaseModel):
            return strategy_for_input_model(bare)
    except TypeError:
        pass
    if bare is str:
        return st.text()
    if bare is int:
        return st.integers()
    if bare is float:
        return st.floats(allow_nan=False)
    if bare is bool:
        return st.booleans()
    try:
        return st.from_type(bare)
    except Exception:
        return st.none()


def strategy_for_input_model(
    model: type[BaseModel],
    path_template: str | None = None,
) -> st.SearchStrategy[BaseModel]:
    """
    Build a Hypothesis strategy that generates instances of the input model.

    Use for GET (query) or POST/PUT/PATCH (body) input. If path_template is
    given (e.g. '/users/{id}'), path param names are inferred; the strategy
    still generates full model instances (path params can be passed separately
    when building the request).
    """
    strategies: dict[str, st.SearchStrategy[Any]] = {}
    for name, field in model.model_fields.items():
        ann = field.annotation
        if ann is not None:
            strategies[name] = _strategy_for_annotation(ann)
        else:
            strategies[name] = st.none()
    return st.builds(model, **strategies)


class _ResponseProtocol(Protocol):
    """Minimal response interface (e.g. Starlette Response)."""

    @property
    def status_code(self) -> int: ...
    @property
    def text(self) -> str: ...
    def json(self) -> object: ...


class _HTTPClientProtocol(Protocol):
    """Protocol for an HTTP client used by test_endpoint (e.g. Starlette TestClient)."""

    def get(self, url: str) -> _ResponseProtocol: ...
    def request(
        self, method: str, url: str, json: object = None
    ) -> _ResponseProtocol: ...
    def delete(self, url: str) -> _ResponseProtocol: ...


def test_endpoint(
    client: _HTTPClientProtocol,
    method: str,
    path: str,
    input_strategy: st.SearchStrategy[BaseModel],
    output_model: type,
    path_params: dict[str, str] | None = None,
    validate_response: bool = True,
    invariants: tuple[Callable[[BaseModel, object], bool], ...] = (),
) -> None:
    """
    Run a property-based test: draw input from input_strategy, call the
    endpoint, assert status and that response conforms to output_model.
    Optional invariants are (input, output) -> bool; all must hold.
    """
    path_params = path_params or {}
    path_params_from_template = {
        k: (path_params.get(k) or "placeholder") for k in _parse_path_params(path)
    }

    @given(input_strategy)
    def _run(input_instance: BaseModel) -> None:
        data = input_instance.model_dump()
        url = path
        for key, val in path_params_from_template.items():
            url = url.replace("{" + key + "}", str(val))
        if method.upper() == "GET":
            from urllib.parse import urlencode

            query = urlencode(data)
            url = f"{url}?{query}" if query else url
            r = client.get(url)
        elif method.upper() in ("POST", "PUT", "PATCH"):
            r = client.request(method.upper(), url, json=data)
        elif method.upper() == "DELETE":
            r = client.delete(url)
        else:
            raise ValueError(f"Unsupported method {method}")
        assert r.status_code in (200, 201, 204), (r.status_code, r.text)
        if r.status_code == 204:
            return
        body = r.json()
        if validate_response:
            from pydantic import TypeAdapter

            adapter: TypeAdapter[Any] = TypeAdapter(output_model)
            adapter.validate_python(body)
        for inv in invariants:
            assert inv(input_instance, body), f"Invariant failed: {inv}"

    _run()
