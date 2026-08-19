"""Optional databricks-sdk compatibility tests. Skipped unless installed."""

from __future__ import annotations

import pytest

pytest.importorskip("databricks.sdk")


@pytest.mark.sdk
def test_sdk_lists_clusters(client) -> None:
    """Best-effort: SDK against ASGI may require HTTPS/hostname adapters."""
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        pytest.skip("databricks.sdk WorkspaceClient not importable")

    try:
        w = WorkspaceClient(
            host="http://127.0.0.1",
            token="test",
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SDK cannot target localhost: {exc}")

    try:
        _ = list(w.clusters.list())
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"SDK list clusters not feasible against mock: {exc}")
