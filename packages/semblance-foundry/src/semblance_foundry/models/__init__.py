"""Pydantic models approximating public Foundry API v2 JSON (hand-authored)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class OntologyV2(CamelModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    rid: str


class ListOntologiesResponse(CamelModel):
    data: list[OntologyV2]


class PropertyTypeV2(CamelModel):
    description: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    data_type: dict[str, Any] = Field(alias="dataType")
    rid: str | None = None


class ObjectTypeV2(CamelModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    status: str = "ACTIVE"
    primary_key: str = Field(alias="primaryKey")
    properties: dict[str, PropertyTypeV2] = Field(default_factory=dict)
    rid: str


class ListObjectTypesResponse(CamelModel):
    data: list[ObjectTypeV2]
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


class OntologyObjectV2(CamelModel):
    """Object properties plus Foundry metadata keys."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ListObjectsResponse(CamelModel):
    data: list[dict[str, Any]]
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


class SearchObjectsRequest(CamelModel):
    where: dict[str, Any] | None = None
    page_size: int | None = Field(default=None, alias="pageSize")
    page_token: str | None = Field(default=None, alias="pageToken")
    select: list[str] | None = None


class ActionTypeV2(CamelModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    rid: str
    status: str = "ACTIVE"


class ListActionTypesResponse(CamelModel):
    data: list[ActionTypeV2]
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


class QueryTypeV2(CamelModel):
    api_name: str = Field(alias="apiName")
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    rid: str


class ListQueryTypesResponse(CamelModel):
    data: list[QueryTypeV2]
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


class ExecuteQueryRequest(CamelModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
