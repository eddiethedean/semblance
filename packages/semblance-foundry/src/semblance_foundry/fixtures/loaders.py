"""Fixture v1 schema and loaders. YAML/JSON is data only — never evaluated."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from semblance_foundry.ids import make_rid
from semblance_foundry.state import (
    ActionTypeRecord,
    FoundryState,
    LinkTypeRecord,
    PropertyTypeRecord,
    QueryTypeRecord,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FixtureProperty(_StrictModel):
    data_type: dict[str, Any] = Field(
        alias="dataType", default_factory=lambda: {"type": "string"}
    )
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None


class FixtureLinkPair(_StrictModel):
    from_key: str = Field(alias="from")
    to_key: str = Field(alias="to")


class FixtureLinkType(_StrictModel):
    api_name: str = Field(alias="apiName")
    from_object_type: str = Field(alias="from")
    to_object_type: str = Field(alias="to")
    objects: list[FixtureLinkPair] = Field(default_factory=list)


class FixtureObjectType(_StrictModel):
    api_name: str = Field(alias="apiName")
    primary_key: str = Field(alias="primaryKey")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    status: str = "ACTIVE"
    properties: dict[str, FixtureProperty] = Field(default_factory=dict)
    objects: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("objects")
    @classmethod
    def objects_are_dicts(cls, value: list[Any]) -> list[dict[str, Any]]:
        for item in value:
            if not isinstance(item, dict):
                raise ValueError("object entries must be mappings")
        return value


class FixtureActionType(_StrictModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class FixtureQueryResult(_StrictModel):
    type: str = "static"
    value: Any = None
    objects: list[dict[str, Any]] | None = None


class FixtureQueryType(_StrictModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    result: FixtureQueryResult | None = None


class FixtureOntology(_StrictModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    rid: str | None = None
    object_types: list[FixtureObjectType] = Field(
        default_factory=list, alias="objectTypes"
    )
    link_types: list[FixtureLinkType] = Field(default_factory=list, alias="linkTypes")
    action_types: list[FixtureActionType] = Field(
        default_factory=list, alias="actionTypes"
    )
    query_types: list[FixtureQueryType] = Field(
        default_factory=list, alias="queryTypes"
    )


class FixtureDocument(_StrictModel):
    version: int
    ontologies: list[FixtureOntology] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def version_is_one(cls, value: int) -> int:
        if value != 1:
            raise ValueError("only fixture version 1 is supported")
        return value


def parse_fixture(data: dict[str, Any]) -> FixtureDocument:
    return FixtureDocument.model_validate(data)


def load_fixture_file(path: str | Path) -> FixtureDocument:
    raw = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix.lower() in {".yaml", ".yml"}:
        loaded = yaml.safe_load(raw)
    else:
        import json

        loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("fixture root must be a mapping")
    return parse_fixture(loaded)


def apply_fixture(doc: FixtureDocument, state: FoundryState) -> None:
    seed = state.seed
    for ont in doc.ontologies:
        state.add_ontology(
            ont.api_name,
            display_name=ont.display_name,
            description=ont.description,
            rid=ont.rid,
        )
        for ot in ont.object_types:
            props: dict[str, PropertyTypeRecord] = {}
            inferred: dict[str, FixtureProperty] = dict(ot.properties)
            if not inferred and ot.objects:
                for prop_name in ot.objects[0]:
                    inferred[str(prop_name)] = FixtureProperty()
            for name, prop in inferred.items():
                props[name] = PropertyTypeRecord(
                    api_name=name,
                    data_type=prop.data_type,
                    display_name=prop.display_name or name,
                    description=prop.description,
                    rid=make_rid(
                        "property",
                        f"{ont.api_name}:{ot.api_name}:{name}",
                        seed,
                    ),
                )
            if ot.primary_key not in props:
                props[ot.primary_key] = PropertyTypeRecord(
                    api_name=ot.primary_key,
                    data_type={"type": "string"},
                    display_name=ot.primary_key,
                    rid=make_rid(
                        "property",
                        f"{ont.api_name}:{ot.api_name}:{ot.primary_key}",
                        seed,
                    ),
                )
            state.add_object_type(
                ont.api_name,
                ot.api_name,
                ot.primary_key,
                display_name=ot.display_name,
                description=ot.description,
                status=ot.status,
                properties=props,
            )
            if ot.objects:
                state.add_objects(ont.api_name, ot.api_name, ot.objects)
        for lt in ont.link_types:
            rec = LinkTypeRecord(
                api_name=lt.api_name,
                ontology=ont.api_name,
                from_object_type=lt.from_object_type,
                to_object_type=lt.to_object_type,
                rid=make_rid("linkType", f"{ont.api_name}:{lt.api_name}", seed),
                pairs=[(p.from_key, p.to_key) for p in lt.objects],
            )
            key = (ont.api_name, lt.api_name)
            if key in state.link_types:
                raise ValueError(
                    f"Duplicate link type {lt.api_name!r} in ontology {ont.api_name!r}"
                )
            state.link_types[key] = rec
        for at in ont.action_types:
            rec_at = ActionTypeRecord(
                api_name=at.api_name,
                ontology=ont.api_name,
                display_name=at.display_name or at.api_name,
                description=at.description,
                rid=make_rid("action-type", f"{ont.api_name}:{at.api_name}", seed),
                parameters=at.parameters,
            )
            key_at = (ont.api_name, at.api_name)
            if key_at in state.action_types:
                raise ValueError(
                    f"Duplicate action type {at.api_name!r} in ontology {ont.api_name!r}"
                )
            state.action_types[key_at] = rec_at
        for qt in ont.query_types:
            static: Any = None
            if qt.result is not None:
                if qt.result.type != "static":
                    raise ValueError(
                        "query result type must be 'static' in fixtures; "
                        "register Python callbacks with register_query()"
                    )
                static = (
                    qt.result.value
                    if qt.result.value is not None
                    else {"data": qt.result.objects or []}
                )
            rec_qt = QueryTypeRecord(
                api_name=qt.api_name,
                ontology=ont.api_name,
                display_name=qt.display_name or qt.api_name,
                description=qt.description,
                rid=make_rid("query-type", f"{ont.api_name}:{qt.api_name}", seed),
                static_result=static,
            )
            key_qt = (ont.api_name, qt.api_name)
            if key_qt in state.query_types:
                raise ValueError(
                    f"Duplicate query type {qt.api_name!r} in ontology {ont.api_name!r}"
                )
            state.query_types[key_qt] = rec_qt
        state.bump_revision()


def bundled_acme_path() -> Path:
    return Path(__file__).resolve().parent / "defaults" / "acme.yaml"
