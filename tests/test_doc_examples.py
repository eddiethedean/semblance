"""Verify documentation examples run and produce valid output."""

import sys
from pathlib import Path

import pytest


def test_run_examples_produces_valid_output():
    """docs/guides/examples/run_examples.py runs all examples without error."""
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "src"))

    # Import and run - avoids subprocess for speed
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_examples",
        root / "docs" / "guides" / "examples" / "run_examples.py",
    )
    run_examples = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_examples)

    results = {}
    for name, fn in run_examples.EXAMPLES:
        try:
            results[name] = fn()
        except Exception as e:
            pytest.fail(f"Example {name!r} failed: {e}")

    # All examples must return non-empty results (no {"error": "..."})
    for name, data in results.items():
        if isinstance(data, dict) and data.get("error"):
            pytest.fail(f"Example {name!r} returned error: {data['error']}")
