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

    def clear(self, path: str | None = None) -> None:
        """Clear store for path, or all paths if path is None."""
        if path is None:
            self._store.clear()
        elif path in self._store:
            del self._store[path]
