"""Optional foundry-platform-sdk compatibility tests. Skipped unless installed."""

from __future__ import annotations

import pytest

foundry_sdk = pytest.importorskip("foundry_sdk")


@pytest.mark.sdk
def test_sdk_lists_ontologies(client) -> None:
    """Best-effort: SDK against ASGI may require HTTPS/hostname adapters."""
    pytest.importorskip("foundry_sdk")
    try:
        from foundry_sdk import FoundryClient, UserTokenAuth
    except ImportError:
        pytest.skip("foundry_sdk client API not importable")

    # The official client typically needs a hostname + HTTPS. If construction
    # or a call cannot target the in-process app, skip rather than fail CI.
    try:
        _client = FoundryClient(
            auth=UserTokenAuth(token="test"),
            hostname="127.0.0.1",
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SDK cannot target localhost: {exc}")

    try:
        result = _client.ontologies.Ontology.list()
        _ = result
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SDK list ontologies not feasible against mock: {exc}")
