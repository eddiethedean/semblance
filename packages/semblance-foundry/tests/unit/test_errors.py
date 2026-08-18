from semblance_foundry.errors import FoundryError, foundry_error_body


def test_error_envelope_shape() -> None:
    body = foundry_error_body(
        error_code="NOT_FOUND",
        error_name="ObjectNotFound",
        error_instance_id="00000000-0000-0000-0000-000000000001",
        parameters={"objectType": "Employee"},
    )
    assert set(body) == {
        "errorCode",
        "errorName",
        "errorInstanceId",
        "parameters",
    }


def test_foundry_error_to_body() -> None:
    err = FoundryError(404, "NOT_FOUND", "OntologyNotFound", {"ontology": "missing"})
    body = err.to_body("abc")
    assert body["errorInstanceId"] == "abc"
    assert body["parameters"]["ontology"] == "missing"
