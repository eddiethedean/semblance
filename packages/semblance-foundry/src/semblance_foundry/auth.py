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

from semblance_foundry.config import FoundryMockConfig
from semblance_foundry.errors import foundry_error_body, next_error_instance_id

REQUEST_ID_HEADER = "X-Request-ID"


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


class FoundryMiddleware(BaseHTTPMiddleware):
    """Auth, request-id, optional latency / error injection / rate limit."""

    def __init__(
        self,
        app: Any,
        config: FoundryMockConfig,
        rng: random.Random,
        error_counter: dict[str, int],
    ) -> None:
        super().__init__(app)
        self._config = config
        self._rng = rng
        self._error_counter = error_counter
        self._limiter = _SlidingWindow()

    def _instance_id(self) -> str:
        self._error_counter["n"] = self._error_counter.get("n", 0) + 1
        return next_error_instance_id(
            self._config.seed, self._error_counter["n"] + 10_000
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming else f"req-{self._config.seed}-{id(request)}"
        request.state.request_id = request_id

        if self._config.rate_limit is not None:
            if not self._limiter.allow(
                request.url.path, request.method, self._config.rate_limit
            ):
                body = foundry_error_body(
                    error_code="PERMISSION_DENIED",
                    error_name="RateLimitExceeded",
                    error_instance_id=self._instance_id(),
                    parameters={},
                )
                response = JSONResponse(status_code=429, content=body)
                response.headers[REQUEST_ID_HEADER] = request_id
                return response

        auth_error = self._check_auth(request)
        if auth_error is not None:
            auth_error.headers[REQUEST_ID_HEADER] = request_id
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
            body = foundry_error_body(
                error_code="INTERNAL",
                error_name="InjectedError",
                error_instance_id=self._instance_id(),
                parameters={"statusCode": status},
            )
            response = JSONResponse(status_code=status, content=body)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response  # type: ignore[no-any-return]

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
                content=foundry_error_body(
                    error_code="UNAUTHORIZED",
                    error_name="InvalidCredentials",
                    error_instance_id=self._instance_id(),
                    parameters={},
                ),
            )
        if mode == "optional":
            return None
        # strict
        if token is None:
            return JSONResponse(
                status_code=401,
                content=foundry_error_body(
                    error_code="UNAUTHORIZED",
                    error_name="MissingCredentials",
                    error_instance_id=self._instance_id(),
                    parameters={},
                ),
            )
        allowed = {g.token for g in self._config.tokens}
        if token not in allowed:
            return JSONResponse(
                status_code=401,
                content=foundry_error_body(
                    error_code="UNAUTHORIZED",
                    error_name="InvalidCredentials",
                    error_instance_id=self._instance_id(),
                    parameters={},
                ),
            )
        return None
