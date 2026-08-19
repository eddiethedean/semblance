import pytest

from semblance_foundry.errors import FoundryError
from semblance_foundry.ids import PageTokenCodec, rid_secret


def test_page_token_round_trip() -> None:
    codec = PageTokenCodec(rid_secret(42))
    token = codec.encode("objects:acme:Employee", 2, 1)
    cursor = codec.decode(token, "objects:acme:Employee")
    assert cursor.offset == 2
    assert cursor.revision == 1
    assert cursor.resource == "objects:acme:Employee"


def test_page_token_tamper_rejected() -> None:
    codec = PageTokenCodec(rid_secret(42))
    token = codec.encode("objects:acme:Employee", 0, 1)
    with pytest.raises(FoundryError) as exc:
        codec.decode(token + "x", "objects:acme:Employee")
    assert exc.value.error_name == "InvalidPageToken"
    assert exc.value.status_code == 400


def test_page_token_wrong_resource() -> None:
    codec = PageTokenCodec(rid_secret(42))
    token = codec.encode("objects:acme:Employee", 0, 1)
    with pytest.raises(FoundryError) as exc:
        codec.decode(token, "objects:acme:Office")
    assert exc.value.error_name == "InvalidPageToken"


def test_page_token_short_sig_rejected() -> None:
    import base64

    codec = PageTokenCodec(rid_secret(42))
    token = codec.encode("objects:acme:Employee", 0, 1)
    padded = token + "=" * (-len(token) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode()).decode()
    payload, _sig = decoded.rsplit("|", 1)
    short = base64.urlsafe_b64encode(f"{payload}|ab".encode()).decode().rstrip("=")
    with pytest.raises(FoundryError) as exc:
        codec.decode(short, "objects:acme:Employee")
    assert exc.value.error_name == "InvalidPageToken"
