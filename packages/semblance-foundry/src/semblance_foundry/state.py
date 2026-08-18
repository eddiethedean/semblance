"""Process-local Foundry ontology graph."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from semblance_foundry.ids import make_rid


@dataclass
class OntologyRecord:
    api_name: str
    display_name: str | None
    description: str | None
    rid: str


@dataclass
class PropertyTypeRecord:
    api_name: str
    data_type: dict[str, Any]
    display_name: str | None = None
    description: str | None = None
    rid: str = ""


@dataclass
class ObjectTypeRecord:
    api_name: str
    ontology: str
    primary_key: str
    display_name: str | None
    description: str | None
    status: str
    rid: str
    properties: dict[str, PropertyTypeRecord] = field(default_factory=dict)


@dataclass
class ObjectRecord:
    ontology: str
    object_type: str
    primary_key: str
    rid: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkTypeRecord:
    api_name: str
    ontology: str
    from_object_type: str
    to_object_type: str
    rid: str
    pairs: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class ActionTypeRecord:
    api_name: str
    ontology: str
    display_name: str | None
    description: str | None
    rid: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryTypeRecord:
    api_name: str
    ontology: str
    display_name: str | None
    description: str | None
    rid: str
    static_result: Any = None


class FoundryState:
    """In-memory ontology graph. No restart durability."""

    def __init__(self, seed: int | None = 42) -> None:
        self.seed = seed
        self.revision = 0
        self.ontologies: dict[str, OntologyRecord] = {}
        self.object_types: dict[tuple[str, str], ObjectTypeRecord] = {}
        self.objects: dict[tuple[str, str, str], ObjectRecord] = {}
        self.link_types: dict[tuple[str, str], LinkTypeRecord] = {}
        self.action_types: dict[tuple[str, str], ActionTypeRecord] = {}
        self.query_types: dict[tuple[str, str], QueryTypeRecord] = {}
        self.query_callbacks: dict[str, Callable[..., Any]] = {}

    def bump_revision(self) -> None:
        self.revision += 1

    def clear(self) -> None:
        self.ontologies.clear()
        self.object_types.clear()
        self.objects.clear()
        self.link_types.clear()
        self.action_types.clear()
        self.query_types.clear()
        self.query_callbacks.clear()
        self.revision = 0

    def resolve_ontology(self, identifier: str) -> OntologyRecord | None:
        if identifier in self.ontologies:
            return self.ontologies[identifier]
        for rec in self.ontologies.values():
            if rec.rid == identifier:
                return rec
        return None

    def list_ontologies(self) -> list[OntologyRecord]:
        return list(self.ontologies.values())

    def add_ontology(
        self,
        api_name: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        rid: str | None = None,
    ) -> OntologyRecord:
        if api_name in self.ontologies:
            raise ValueError(f"Duplicate ontology apiName {api_name!r}")
        rec = OntologyRecord(
            api_name=api_name,
            display_name=display_name or api_name,
            description=description,
            rid=rid or make_rid("ontology", api_name, self.seed),
        )
        self.ontologies[api_name] = rec
        self.bump_revision()
        return rec

    def add_object_type(
        self,
        ontology: str,
        api_name: str,
        primary_key: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
        status: str = "ACTIVE",
        rid: str | None = None,
        properties: dict[str, PropertyTypeRecord] | None = None,
    ) -> ObjectTypeRecord:
        key = (ontology, api_name)
        if key in self.object_types:
            raise ValueError(
                f"Duplicate object type {api_name!r} in ontology {ontology!r}"
            )
        rec = ObjectTypeRecord(
            api_name=api_name,
            ontology=ontology,
            primary_key=primary_key,
            display_name=display_name or api_name,
            description=description,
            status=status,
            rid=rid or make_rid("objectType", f"{ontology}:{api_name}", self.seed),
            properties=properties or {},
        )
        self.object_types[key] = rec
        self.bump_revision()
        return rec

    def add_objects(
        self,
        ontology: str,
        object_type: str,
        objects: list[dict[str, Any]],
    ) -> list[ObjectRecord]:
        ot = self.object_types.get((ontology, object_type))
        if ot is None:
            raise ValueError(
                f"Unknown object type {object_type!r} in ontology {ontology!r}"
            )
        created: list[ObjectRecord] = []
        for props in objects:
            pk = str(props.get(ot.primary_key, ""))
            if not pk:
                raise ValueError(
                    f"Object missing primary key {ot.primary_key!r} for {object_type!r}"
                )
            key = (ontology, object_type, pk)
            if key in self.objects:
                raise ValueError(
                    f"Duplicate primary key {pk!r} for {object_type!r} "
                    f"in ontology {ontology!r}"
                )
            rec = ObjectRecord(
                ontology=ontology,
                object_type=object_type,
                primary_key=pk,
                rid=make_rid("object", f"{ontology}:{object_type}:{pk}", self.seed),
                properties=dict(props),
            )
            self.objects[key] = rec
            created.append(rec)
        self.bump_revision()
        return created

    def list_object_types(self, ontology: str) -> list[ObjectTypeRecord]:
        return [v for k, v in self.object_types.items() if k[0] == ontology]

    def get_object_type(
        self, ontology: str, object_type: str
    ) -> ObjectTypeRecord | None:
        return self.object_types.get((ontology, object_type))

    def list_objects(self, ontology: str, object_type: str) -> list[ObjectRecord]:
        items = [
            v
            for k, v in self.objects.items()
            if k[0] == ontology and k[1] == object_type
        ]
        items.sort(key=lambda o: o.primary_key)
        return items

    def get_object(
        self, ontology: str, object_type: str, primary_key: str
    ) -> ObjectRecord | None:
        return self.objects.get((ontology, object_type, primary_key))

    def list_link_types(self, ontology: str) -> list[LinkTypeRecord]:
        return [v for k, v in self.link_types.items() if k[0] == ontology]

    def get_link_type(self, ontology: str, api_name: str) -> LinkTypeRecord | None:
        return self.link_types.get((ontology, api_name))

    def linked_objects(
        self,
        ontology: str,
        object_type: str,
        primary_key: str,
        link_type: str,
    ) -> list[ObjectRecord]:
        lt = self.get_link_type(ontology, link_type)
        if lt is None:
            return []
        if lt.from_object_type != object_type:
            return []
        targets = [to_pk for from_pk, to_pk in lt.pairs if from_pk == primary_key]
        result: list[ObjectRecord] = []
        for to_pk in targets:
            rec = self.get_object(ontology, lt.to_object_type, to_pk)
            if rec is not None:
                result.append(rec)
        return result

    def list_action_types(self, ontology: str) -> list[ActionTypeRecord]:
        return [v for k, v in self.action_types.items() if k[0] == ontology]

    def get_action_type(self, ontology: str, api_name: str) -> ActionTypeRecord | None:
        return self.action_types.get((ontology, api_name))

    def list_query_types(self, ontology: str) -> list[QueryTypeRecord]:
        return [v for k, v in self.query_types.items() if k[0] == ontology]

    def get_query_type(self, ontology: str, api_name: str) -> QueryTypeRecord | None:
        return self.query_types.get((ontology, api_name))

    def register_query(self, api_name: str, fn: Callable[..., Any]) -> None:
        self.query_callbacks[api_name] = fn


class OntologyMutations:
    """Test helper surface: ``foundry.ontologies.add_objects(...)``."""

    def __init__(self, state: FoundryState) -> None:
        self._state = state

    def add_objects(
        self,
        ontology: str,
        object_type: str,
        objects: list[dict[str, Any]],
    ) -> list[ObjectRecord]:
        return self._state.add_objects(ontology, object_type, objects)
