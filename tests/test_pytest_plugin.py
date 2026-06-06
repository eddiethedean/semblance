"""Tests for the Semblance pytest plugin."""

import importlib.util

import pytest

hypothesis_installed = importlib.util.find_spec("hypothesis") is not None


@pytest.mark.semblance(app="tests.sample_app:api")
def test_pytest_plugin_semblance_client(semblance_client):
    r = semblance_client.get("/users?name=plugin_test")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == "plugin_test"


@pytest.mark.skipif(not hypothesis_installed, reason="hypothesis not installed")
@pytest.mark.semblance_property_tests(app="tests.sample_app:api")
def test_semblance_property_per_endpoint(
    semblance_client,
    semblance_api,
    endpoint_path,
    endpoint_method,
):
    spec = semblance_api.get_spec(endpoint_path, endpoint_method)
    assert spec is not None
    if spec.output_annotation is None:
        pytest.skip("DELETE with no output model")
    from semblance.property_testing import strategy_for_input_model, test_endpoint

    strategy = strategy_for_input_model(spec.input_model)
    test_endpoint(
        semblance_client,
        endpoint_method,
        endpoint_path,
        strategy,
        spec.output_annotation,
        validate_response=True,
    )
