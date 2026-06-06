"""Tests for semblance.state - StatefulStore."""

from pydantic import BaseModel

from semblance.state import StatefulStore


def test_add_auto_generates_id_when_missing():
    class ModelWithId(BaseModel):
        id: str = ""
        name: str

    store = StatefulStore()
    result = store.add("/items", ModelWithId(name="alice"))
    assert result.id != ""
    assert result.name == "alice"


def test_add_preserves_existing_id():
    class ModelWithId(BaseModel):
        id: str = ""
        name: str

    store = StatefulStore()
    result = store.add("/items", ModelWithId(id="custom-123", name="alice"))
    assert result.id == "custom-123"


def test_add_model_without_id_field():
    class ModelNoId(BaseModel):
        name: str

    store = StatefulStore()
    result = store.add("/items", ModelNoId(name="bob"))
    assert result.name == "bob"


def test_get_all_empty_path_returns_empty_list():
    store = StatefulStore()
    assert store.get_all("/nonexistent") == []


def test_get_all_returns_stored_items():
    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="a"))
    store.add("/items", Item(name="b"))
    result = store.get_all("/items")
    assert len(result) == 2
    assert [r.name for r in result] == ["a", "b"]


def test_get_by_id_returns_matching_item():
    class Item(BaseModel):
        id: str = ""
        name: str

    store = StatefulStore()
    added = store.add("/items", Item(name="x"))
    found = store.get_by_id("/items", added.id, "id")
    assert found is not None
    assert found.name == "x"


def test_get_by_id_returns_none_when_missing():
    class Item(BaseModel):
        id: str = "1"
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="x"))
    assert store.get_by_id("/items", "missing", "id") is None


def test_update_replaces_matching_item():
    class Item(BaseModel):
        id: str = "1"
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="before"))
    updated = store.update("/items", "1", Item(id="1", name="after"), "id")
    assert updated is not None
    assert updated.name == "after"
    assert store.get_by_id("/items", "1", "id").name == "after"


def test_update_returns_none_when_missing():
    class Item(BaseModel):
        id: str = "1"
        name: str

    store = StatefulStore()
    assert store.update("/items", "1", Item(name="x"), "id") is None


def test_remove_deletes_matching_item():
    class Item(BaseModel):
        id: str = "1"
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="x"))
    assert store.remove("/items", "1", "id") is True
    assert store.get_all("/items") == []


def test_remove_returns_false_when_missing():
    store = StatefulStore()
    assert store.remove("/items", "1", "id") is False


def test_clear_path_removes_only_that_path():
    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="x"))
    store.add("/other", Item(name="y"))
    store.clear("/items")
    assert store.get_all("/items") == []
    assert len(store.get_all("/other")) == 1


def test_clear_none_removes_all():
    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/a", Item(name="x"))
    store.add("/b", Item(name="y"))
    store.clear(None)
    assert store.get_all("/a") == []
    assert store.get_all("/b") == []
