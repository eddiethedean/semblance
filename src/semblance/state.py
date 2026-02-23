"""
Optional stateful mode: persist created items across requests.

When SemblanceAPI(stateful=True), POST endpoints store created instances
and GET list endpoints return stored instances. State is process-local.
"""

import uuid

from pydantic import BaseModel


class StatefulStore:
    """In-memory store for created instances, keyed by path."""

    def __init__(self) -> None:
        self._store: dict[str, list[BaseModel]] = {}

    def add(self, path: str, instance: BaseModel) -> BaseModel:
        """Add an instance to the store. Ensures id field if present. Returns the instance."""
        if "id" in type(instance).model_fields:
            data = instance.model_dump()
            if data.get("id") in (None, ""):
                data["id"] = str(uuid.uuid4())
                model_cls = type(instance)
                instance = model_cls.model_validate(data)

        if path not in self._store:
            self._store[path] = []
        self._store[path].append(instance)
        return instance

    def get_all(self, path: str) -> list[BaseModel]:
        """Return all stored instances for path."""
        return list(self._store.get(path, []))

    def get_by_id(
        self, collection_path: str, id_value: str, id_field: str = "id"
    ) -> BaseModel | None:
        """Find item in collection whose id_field equals id_value. Return None if not found."""
        items = self._store.get(collection_path, [])
        for item in items:
            if getattr(item, id_field, None) == id_value:
                return item
        return None

    def update(
        self,
        collection_path: str,
        id_value: str,
        instance: BaseModel,
        id_field: str = "id",
    ) -> BaseModel | None:
        """Replace item with matching id with instance. Return updated instance or None."""
        if collection_path not in self._store:
            return None
        items = self._store[collection_path]
        for i, item in enumerate(items):
            if getattr(item, id_field, None) == id_value:
                items[i] = instance
                return instance
        return None

    def remove(
        self, collection_path: str, id_value: str, id_field: str = "id"
    ) -> bool:
        """Remove item with matching id. Return True if found and removed."""
        if collection_path not in self._store:
            return False
        items = self._store[collection_path]
        for i, item in enumerate(items):
            if getattr(item, id_field, None) == id_value:
                items.pop(i)
                return True
        return False

    def clear(self, path: str | None = None) -> None:
        """Clear store for path, or all paths if path is None."""
        if path is None:
            self._store.clear()
        elif path in self._store:
            del self._store[path]
