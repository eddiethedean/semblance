"""Deterministic Foundry-like RIDs and opaque page tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass


def rid_secret(seed: int | None) -> bytes:
    """Derive a process-local HMAC key from the mock seed."""
    material = f"semblance-foundry:{seed if seed is not None else 'none'}"
    return hashlib.sha256(material.encode()).digest()


def make_rid(kind: str, identity: str, seed: int | None = 42) -> str:
    """Build a stable Foundry-like RID from kind + identity."""
    digest = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"semblance-foundry:{seed}:{kind}:{identity}",
    )
    return f"ri.ontology.main.{kind}.{digest}"


@dataclass(frozen=True)
class PageCursor:
    """Decoded page-token payload."""

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
        from semblance_foundry.errors import FoundryError

        try:
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode()).decode()
            payload, sig = decoded.rsplit("|", 1)
            expected = hmac.new(
                self._secret, payload.encode(), hashlib.sha256
            ).hexdigest()[:16]
            if not hmac.compare_digest(sig, expected):
                raise ValueError("checksum mismatch")
            data = json.loads(payload)
            resource = str(data["r"])
            offset = int(data["o"])
            revision = int(data["v"])
        except (ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise FoundryError(
                status_code=400,
                error_code="INVALID_ARGUMENT",
                error_name="InvalidPageToken",
                parameters={"pageToken": "<redacted>"},
            ) from exc
        if resource != expected_resource:
            raise FoundryError(
                status_code=400,
                error_code="INVALID_ARGUMENT",
                error_name="InvalidPageToken",
                parameters={"pageToken": "<redacted>"},
            )
        if offset < 0:
            raise FoundryError(
                status_code=400,
                error_code="INVALID_ARGUMENT",
                error_name="InvalidPageToken",
                parameters={"pageToken": "<redacted>"},
            )
        return PageCursor(resource=resource, offset=offset, revision=revision)
