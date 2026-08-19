import pytest

from semblance_databricks.errors import DatabricksError
from semblance_databricks.ids import PageTokenCodec, token_secret


def test_page_token_round_trip() -> None:
    codec = PageTokenCodec(token_secret(42))
    token = codec.encode("clusters", 2, 1)
    cursor = codec.decode(token, "clusters")
    assert cursor.offset == 2
    assert cursor.revision == 1
    assert cursor.resource == "clusters"


def test_page_token_tamper_rejected() -> None:
    codec = PageTokenCodec(token_secret(42))
    token = codec.encode("clusters", 0, 1)
    with pytest.raises(DatabricksError) as exc:
        codec.decode(token + "x", "clusters")
    assert exc.value.error_code == "INVALID_PARAMETER_VALUE"
    assert exc.value.status_code == 400


def test_page_token_wrong_resource() -> None:
    codec = PageTokenCodec(token_secret(42))
    token = codec.encode("clusters", 0, 1)
    with pytest.raises(DatabricksError) as exc:
        codec.decode(token, "jobs")
    assert exc.value.error_code == "INVALID_PARAMETER_VALUE"


def test_page_token_short_sig_rejected() -> None:
    import base64

    codec = PageTokenCodec(token_secret(42))
    token = codec.encode("clusters", 0, 1)
    padded = token + "=" * (-len(token) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode()).decode()
    payload, _sig = decoded.rsplit("|", 1)
    short = base64.urlsafe_b64encode(f"{payload}|ab".encode()).decode().rstrip("=")
    with pytest.raises(DatabricksError) as exc:
        codec.decode(short, "clusters")
    assert exc.value.status_code == 400
