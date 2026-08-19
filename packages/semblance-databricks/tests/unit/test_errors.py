from semblance_databricks.errors import DatabricksError, databricks_error_body


def test_error_envelope_shape() -> None:
    body = databricks_error_body("RESOURCE_DOES_NOT_EXIST", "missing")
    assert set(body) == {"error_code", "message"}
    assert "token" not in body


def test_databricks_error_to_body() -> None:
    err = DatabricksError(
        404, "RESOURCE_DOES_NOT_EXIST", "Cluster secret-token not found"
    )
    body = err.to_body()
    assert body["error_code"] == "RESOURCE_DOES_NOT_EXIST"
    assert "secret-token" in body["message"]
