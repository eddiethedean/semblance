import json
from pathlib import Path

import pytest

from semblance.fixture_json import load_json_file, pick_where, resolve_pointer


def test_resolve_pointer_and_where(tmp_path: Path) -> None:
    path = tmp_path / "f.json"
    path.write_text(
        json.dumps({"items": [{"id": "1", "k": "a"}, {"id": "2", "k": "b"}]}),
        encoding="utf-8",
    )
    doc = load_json_file(str(path))
    assert resolve_pointer(doc, "")["items"][0]["id"] == "1"
    assert resolve_pointer(doc, "items/1/id") == "2"
    picked = pick_where(doc["items"], {"k": "office"}, {"office": "b"})
    assert picked["id"] == "2"
    with pytest.raises(KeyError):
        resolve_pointer(doc, "items/9")
    with pytest.raises(KeyError):
        resolve_pointer(doc, "nope")
    with pytest.raises(KeyError):
        resolve_pointer("x", "0")
    with pytest.raises(KeyError):
        pick_where(doc["items"], {"k": "office"}, {"office": "z"})
    with pytest.raises(KeyError):
        resolve_pointer(doc, "items/nope")
