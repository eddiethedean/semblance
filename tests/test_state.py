"""Tests for semblance.state - StatefulStore."""

from pydantic import BaseModel

from semblance.state import StatefulStore


def test_add_auto_generates_id_when_missing():
    """StatefulStore.add generates id when model has id field and it is empty."""

    class ModelWithId(BaseModel):
        id: str = ""
        name: str

    store = StatefulStore()
    instance = ModelWithId(name="alice")
    result = store.add("/items", instance)
    assert result.id != ""
    assert result.name == "alice"


def test_add_preserves_existing_id():
    """StatefulStore.add preserves id when already set."""

    class ModelWithId(BaseModel):
        id: str = ""
        name: str

    store = StatefulStore()
    instance = ModelWithId(id="custom-123", name="alice")
    result = store.add("/items", instance)
    assert result.id == "custom-123"
    assert result.name == "alice"


def test_add_model_without_id_field():
    """StatefulStore.add works for models without id field."""

    class ModelNoId(BaseModel):
        name: str

    store = StatefulStore()
    instance = ModelNoId(name="bob")
    result = store.add("/items", instance)
    assert result.name == "bob"
    assert not hasattr(result, "id") or getattr(result, "id", None) is None


def test_get_all_empty_path_returns_empty_list():
    """StatefulStore.get_all returns [] for path with no items."""
    store = StatefulStore()
    result = store.get_all("/nonexistent")
    assert result == []


def test_get_all_returns_stored_items():
    """StatefulStore.get_all returns all items for path."""

    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="a"))
    store.add("/items", Item(name="b"))
    result = store.get_all("/items")
    assert len(result) == 2
    assert [r.name for r in result] == ["a", "b"]


def test_clear_path_removes_only_that_path():
    """StatefulStore.clear(path) removes only that path."""

    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/items", Item(name="x"))
    store.add("/other", Item(name="y"))
    store.clear("/items")
    assert store.get_all("/items") == []
    assert len(store.get_all("/other")) == 1


def test_clear_none_removes_all():
    """StatefulStore.clear(None) clears entire store."""

    class Item(BaseModel):
        name: str

    store = StatefulStore()
    store.add("/a", Item(name="x"))
    store.add("/b", Item(name="y"))
    store.clear(None)
    assert store.get_all("/a") == []
    assert store.get_all("/b") == []
