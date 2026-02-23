"""
Rate limiting simulation for endpoints.

Sliding-window: at most N requests per second per (path, method).
Per-process, in-memory; for simulation only.
"""

import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """Sliding-window rate limiter keyed by (path, method)."""

    def __init__(self) -> None:
        self._timestamps: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._lock = Lock()

    def check_and_record(self, path: str, method: str, limit: float) -> bool:
        """
        Record a request and return True if under limit, False if over limit.

        Uses a 1-second sliding window: requests older than 1 second are dropped.
        """
        if limit <= 0:
            return True
        now = time.monotonic()
        key = (path, method)
        with self._lock:
            ts_list = self._timestamps[key]
            # Drop timestamps older than 1 second
            ts_list[:] = [t for t in ts_list if now - t < 1.0]
            if len(ts_list) >= limit:
                return False
            ts_list.append(now)
        return True


_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    """Return the global rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
