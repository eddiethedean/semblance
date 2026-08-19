"""Deterministic resource IDs and opaque page tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass

from semblance_databricks.errors import DatabricksError


def token_secret(seed: int | None) -> bytes:
    material = f"semblance-databricks:{seed if seed is not None else 'none'}"
    return hashlib.sha256(material.encode()).digest()


def make_id(kind: str, identity: str, seed: int | None = 42) -> str:
    digest = hashlib.sha256(
        f"semblance-databricks:{seed}:{kind}:{identity}".encode()
    ).hexdigest()[:12]
    if kind == "cluster":
        return f"0101-{digest[:8]}-{digest[8:]}"
    if kind == "job":
        return str(int(digest[:8], 16) % 10_000_000 + 1000)
    if kind == "run":
        return str(int(digest[:8], 16) % 10_000_000 + 2000)
    if kind == "warehouse":
        return digest
    return digest


@dataclass(frozen=True)
class PageCursor:
    resource: str
    offset: int
    revision: int


class PageTokenCodec:
    """URL-safe checksummed page tokens. Opaque to clients."""

    def __init__(self, secret: bytes) -> None:
        self._secret = secret

    def encode(self, resource: str, offset: int, revision: int) -> str:
        payload = json.dumps(
            {"r": resource, "o": offset, "v": revision},
            separators=(",", ":"),
        )
        sig = hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()[:16]
        raw = f"{payload}|{sig}".encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    def decode(self, token: str, expected_resource: str) -> PageCursor:
        try:
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode()).decode()
            payload, sig = decoded.rsplit("|", 1)
            expected = hmac.new(
                self._secret, payload.encode(), hashlib.sha256
            ).hexdigest()[:16]
            if len(sig) != len(expected) or not hmac.compare_digest(sig, expected):
                raise ValueError("checksum mismatch")
            data = json.loads(payload)
            resource = str(data["r"])
            offset = int(data["o"])
            revision = int(data["v"])
        except (
            ValueError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as exc:
            raise DatabricksError(
                400,
                "INVALID_PARAMETER_VALUE",
                "Invalid page token",
            ) from exc
        if resource != expected_resource or offset < 0:
            raise DatabricksError(
                400,
                "INVALID_PARAMETER_VALUE",
                "Invalid page token",
            )
        return PageCursor(resource=resource, offset=offset, revision=revision)
