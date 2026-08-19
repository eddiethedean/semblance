"""Auth, request-id, latency, error injection, and rate-limit middleware."""

from __future__ import annotations

import asyncio
import random
import time
from collections import defaultdict
from collections.abc import Callable
from threading import Lock
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from semblance_databricks.config import DatabricksMockConfig
from semblance_databricks.errors import databricks_error_body

REQUEST_ID_HEADER = "x-databricks-request-id"
ORG_ID_HEADER = "x-databricks-org-id"


class _SlidingWindow:
    def __init__(self) -> None:
        self._timestamps: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, path: str, method: str, limit: float) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        key = (path, method)
        with self._lock:
            ts_list = self._timestamps[key]
            ts_list[:] = [t for t in ts_list if now - t < 1.0]
            if len(ts_list) >= limit:
                return False
            ts_list.append(now)
        return True


def _bearer_token(header: str | None) -> str | None:
    if header is None or header == "":
        return None
    parts = header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("malformed")
    token = parts[1].strip()
    if not token:
        raise ValueError("empty")
    return token


class DatabricksMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        config: DatabricksMockConfig,
        rng: random.Random,
    ) -> None:
        super().__init__(app)
        self._config = config
        self._rng = rng
        self._limiter = _SlidingWindow()
        self._req_n = 0

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        self._req_n += 1
        request_id = incoming if incoming else f"req-{self._config.seed}-{self._req_n}"
        request.state.request_id = request_id

        if self._config.rate_limit is not None:
            if not self._limiter.allow(
                request.url.path, request.method, self._config.rate_limit
            ):
                response = JSONResponse(
                    status_code=429,
                    content=databricks_error_body(
                        "REQUEST_LIMIT_EXCEEDED", "Rate limit exceeded"
                    ),
                )
                self._stamp(response, request_id)
                return response

        auth_error = self._check_auth(request)
        if auth_error is not None:
            self._stamp(auth_error, request_id)
            return auth_error

        if self._config.latency_ms or self._config.jitter_ms:
            delay = self._config.latency_ms / 1000.0
            if self._config.jitter_ms:
                delay += self._rng.uniform(0, self._config.jitter_ms) / 1000.0
            if delay > 0:
                await asyncio.sleep(delay)

        if self._config.error_rate > 0 and self._rng.random() < self._config.error_rate:
            codes = self._config.error_codes or [500]
            status = self._rng.choice(codes)
            response = JSONResponse(
                status_code=status,
                content=databricks_error_body("INTERNAL_ERROR", "Injected error"),
            )
            self._stamp(response, request_id)
            return response

        response = await call_next(request)
        self._stamp(response, request_id)
        return response  # type: ignore[no-any-return]

    def _stamp(self, response: Response, request_id: str) -> None:
        response.headers[REQUEST_ID_HEADER] = request_id
        if self._config.org_id:
            response.headers[ORG_ID_HEADER] = self._config.org_id

    def _check_auth(self, request: Request) -> JSONResponse | None:
        mode = self._config.auth
        if mode == "disabled":
            return None
        header = request.headers.get("authorization")
        try:
            token = _bearer_token(header)
        except ValueError:
            return JSONResponse(
                status_code=401,
                content=databricks_error_body("UNAUTHENTICATED", "Invalid credentials"),
            )
        if mode == "optional":
            return None
        if token is None:
            return JSONResponse(
                status_code=401,
                content=databricks_error_body("UNAUTHENTICATED", "Missing credentials"),
            )
        allowed = {g.token for g in self._config.tokens}
        if token not in allowed:
            return JSONResponse(
                status_code=401,
                content=databricks_error_body("UNAUTHENTICATED", "Invalid credentials"),
            )
        return None
