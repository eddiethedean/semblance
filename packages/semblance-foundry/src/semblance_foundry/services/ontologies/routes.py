"""Ontology-read HTTP handlers for Foundry API v2."""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

from fastapi import APIRouter, Query, Request

from semblance_foundry.errors import FoundryError
from semblance_foundry.ids import PageTokenCodec
from semblance_foundry.models import (
    ActionTypeV2,
    ExecuteQueryRequest,
    ListActionTypesResponse,
    ListObjectsResponse,
    ListObjectTypesResponse,
    ListOntologiesResponse,
    ListQueryTypesResponse,
    ObjectTypeV2,
    OntologyV2,
    PropertyTypeV2,
    QueryTypeV2,
    SearchObjectsRequest,
)
from semblance_foundry.pagination import paginate
from semblance_foundry.state import (
    ActionTypeRecord,
    FoundryState,
    ObjectRecord,
    ObjectTypeRecord,
    OntologyRecord,
    QueryTypeRecord,
)


def _mock(request: Request) -> Any:
    return request.app.state.foundry_mock


def _state(request: Request) -> FoundryState:
    return cast(FoundryState, _mock(request).state)


def _codec(request: Request) -> PageTokenCodec:
    return cast(PageTokenCodec, _mock(request).page_token_codec)


def _page_defaults(request: Request) -> tuple[int, int]:
    cfg = _mock(request).config
    return cfg.default_page_size, cfg.max_page_size


def _require_ontology(state: FoundryState, ontology: str) -> OntologyRecord:
    rec = state.resolve_ontology(ontology)
    if rec is None:
        raise FoundryError(
            status_code=404,
            error_code="NOT_FOUND",
            error_name="OntologyNotFound",
            parameters={"ontology": ontology},
        )
    return rec


def _ontology_v2(rec: OntologyRecord) -> OntologyV2:
    return OntologyV2(
        apiName=rec.api_name,
        displayName=rec.display_name,
        description=rec.description,
        rid=rec.rid,
    )


def _object_type_v2(rec: ObjectTypeRecord) -> ObjectTypeV2:
    props = {
        name: PropertyTypeV2(
            description=p.description,
            displayName=p.display_name,
            dataType=p.data_type,
            rid=p.rid,
        )
        for name, p in rec.properties.items()
    }
    return ObjectTypeV2(
        apiName=rec.api_name,
        displayName=rec.display_name,
        description=rec.description,
        status=rec.status,
        primaryKey=rec.primary_key,
        properties=props,
        rid=rec.rid,
    )


def _object_payload(
    rec: ObjectRecord, ot: ObjectTypeRecord, select: list[str] | None
) -> dict[str, Any]:
    keys = list(rec.properties.keys())
    if select:
        allowed = set(select) | {ot.primary_key}
        keys = [k for k in keys if k in allowed]
    payload: dict[str, Any] = {
        "__rid": rec.rid,
        "__primaryKey": rec.primary_key,
    }
    for key in keys:
        payload[key] = rec.properties.get(key)
    return payload


def _match_where(obj: dict[str, Any], where: dict[str, Any] | None) -> bool:
    if not where:
        return True
    typ = where.get("type")
    if typ == "eq":
        field = where.get("field")
        return obj.get(str(field)) == where.get("value")
    if typ == "and":
        clauses = where.get("value") or where.get("items") or []
        if not isinstance(clauses, list):
            raise FoundryError(
                status_code=400,
                error_code="INVALID_ARGUMENT",
                error_name="InvalidQuery",
                parameters={"reason": "and.value must be a list"},
            )
        return all(_match_where(obj, c) for c in clauses if isinstance(c, dict))
    raise FoundryError(
        status_code=400,
        error_code="INVALID_ARGUMENT",
        error_name="InvalidQuery",
        parameters={"type": typ, "reason": "only eq and and are supported"},
    )


def _action_v2(rec: ActionTypeRecord) -> ActionTypeV2:
    return ActionTypeV2(
        apiName=rec.api_name,
        displayName=rec.display_name,
        description=rec.description,
        parameters=rec.parameters,
        rid=rec.rid,
    )


def _query_v2(rec: QueryTypeRecord) -> QueryTypeV2:
    return QueryTypeV2(
        apiName=rec.api_name,
        displayName=rec.display_name,
        description=rec.description,
        rid=rec.rid,
    )


def _unsupported(request: Request, operation: str) -> None:
    if _mock(request).config.auth == "strict":
        raise FoundryError(
            status_code=501,
            error_code="UNKNOWN",
            error_name="UnsupportedOperation",
            parameters={"operation": operation},
        )
    raise FoundryError(
        status_code=404,
        error_code="NOT_FOUND",
        error_name="NotFound",
        parameters={"operation": operation},
    )


def create_ontology_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/v2/ontologies", response_model=ListOntologiesResponse)
    def list_ontologies(request: Request) -> ListOntologiesResponse:
        state = _state(request)
        data = [_ontology_v2(o) for o in state.list_ontologies()]
        return ListOntologiesResponse(data=data)

    @router.get(
        "/api/v2/ontologies/{ontology}",
        response_model=OntologyV2,
    )
    def get_ontology(request: Request, ontology: str) -> OntologyV2:
        rec = _require_ontology(_state(request), ontology)
        return _ontology_v2(rec)

    @router.get(
        "/api/v2/ontologies/{ontology}/objectTypes",
        response_model=ListObjectTypesResponse,
        response_model_exclude_none=True,
    )
    def list_object_types(
        request: Request,
        ontology: str,
        page_size: int | None = Query(default=None, alias="pageSize"),
        page_token: str | None = Query(default=None, alias="pageToken"),
    ) -> ListObjectTypesResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        items = state.list_object_types(ont.api_name)
        default_ps, max_ps = _page_defaults(request)
        page, token = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource=f"objectTypes:{ont.api_name}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListObjectTypesResponse(
            data=[_object_type_v2(i) for i in page],
            nextPageToken=token,
        )

    @router.get(
        "/api/v2/ontologies/{ontology}/objectTypes/{objectType}",
        response_model=ObjectTypeV2,
    )
    def get_object_type(
        request: Request, ontology: str, objectType: str
    ) -> ObjectTypeV2:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        rec = state.get_object_type(ont.api_name, objectType)
        if rec is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectTypeNotFound",
                parameters={"ontology": ontology, "objectType": objectType},
            )
        return _object_type_v2(rec)

    @router.get(
        "/api/v2/ontologies/{ontology}/objects/{objectType}",
        response_model=ListObjectsResponse,
        response_model_exclude_none=True,
    )
    def list_objects(
        request: Request,
        ontology: str,
        objectType: str,
        page_size: int | None = Query(default=None, alias="pageSize"),
        page_token: str | None = Query(default=None, alias="pageToken"),
        select: list[str] | None = Query(default=None),
    ) -> ListObjectsResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        ot = state.get_object_type(ont.api_name, objectType)
        if ot is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectTypeNotFound",
                parameters={"ontology": ontology, "objectType": objectType},
            )
        items = state.list_objects(ont.api_name, objectType)
        default_ps, max_ps = _page_defaults(request)
        page, token = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource=f"objects:{ont.api_name}:{objectType}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListObjectsResponse(
            data=[_object_payload(o, ot, select) for o in page],
            nextPageToken=token,
        )

    @router.post(
        "/api/v2/ontologies/{ontology}/objects/{objectType}/search",
        response_model=ListObjectsResponse,
        response_model_exclude_none=True,
    )
    def search_objects(
        request: Request,
        ontology: str,
        objectType: str,
        body: SearchObjectsRequest,
    ) -> ListObjectsResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        ot = state.get_object_type(ont.api_name, objectType)
        if ot is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectTypeNotFound",
                parameters={"ontology": ontology, "objectType": objectType},
            )
        items = [
            o
            for o in state.list_objects(ont.api_name, objectType)
            if _match_where(o.properties, body.where)
        ]
        default_ps, max_ps = _page_defaults(request)
        where_blob = json.dumps(
            {"where": body.where, "select": body.select},
            sort_keys=True,
            default=str,
        )
        where_digest = hashlib.sha256(where_blob.encode()).hexdigest()[:16]
        page, token = paginate(
            items,
            page_size=body.page_size,
            page_token=body.page_token,
            resource=f"search:{ont.api_name}:{objectType}:{where_digest}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListObjectsResponse(
            data=[_object_payload(o, ot, body.select) for o in page],
            nextPageToken=token,
        )

    @router.get(
        "/api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/links/{linkType}",
        response_model=ListObjectsResponse,
        response_model_exclude_none=True,
    )
    def list_linked_objects(
        request: Request,
        ontology: str,
        objectType: str,
        primaryKey: str,
        linkType: str,
        page_size: int | None = Query(default=None, alias="pageSize"),
        page_token: str | None = Query(default=None, alias="pageToken"),
        select: list[str] | None = Query(default=None),
    ) -> ListObjectsResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        if state.get_object(ont.api_name, objectType, primaryKey) is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectNotFound",
                parameters={
                    "objectType": objectType,
                    "primaryKey": primaryKey,
                },
            )
        lt = state.get_link_type(ont.api_name, linkType)
        if lt is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="LinkTypeNotFound",
                parameters={"linkType": linkType},
            )
        to_ot = state.get_object_type(ont.api_name, lt.to_object_type)
        if to_ot is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectTypeNotFound",
                parameters={"objectType": lt.to_object_type},
            )
        items = state.linked_objects(ont.api_name, objectType, primaryKey, linkType)
        default_ps, max_ps = _page_defaults(request)
        page, token = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource=f"links:{ont.api_name}:{objectType}:{primaryKey}:{linkType}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListObjectsResponse(
            data=[_object_payload(o, to_ot, select) for o in page],
            nextPageToken=token,
        )

    @router.get(
        "/api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}",
        response_model=None,
    )
    def get_object(
        request: Request,
        ontology: str,
        objectType: str,
        primaryKey: str,
        select: list[str] | None = Query(default=None),
    ) -> dict[str, Any]:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        ot = state.get_object_type(ont.api_name, objectType)
        if ot is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectTypeNotFound",
                parameters={"ontology": ontology, "objectType": objectType},
            )
        rec = state.get_object(ont.api_name, objectType, primaryKey)
        if rec is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ObjectNotFound",
                parameters={
                    "objectType": objectType,
                    "primaryKey": primaryKey,
                },
            )
        return _object_payload(rec, ot, select)

    @router.get(
        "/api/v2/ontologies/{ontology}/actionTypes",
        response_model=ListActionTypesResponse,
        response_model_exclude_none=True,
    )
    def list_action_types(
        request: Request,
        ontology: str,
        page_size: int | None = Query(default=None, alias="pageSize"),
        page_token: str | None = Query(default=None, alias="pageToken"),
    ) -> ListActionTypesResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        items = state.list_action_types(ont.api_name)
        default_ps, max_ps = _page_defaults(request)
        page, token = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource=f"actionTypes:{ont.api_name}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListActionTypesResponse(
            data=[_action_v2(i) for i in page],
            nextPageToken=token,
        )

    @router.get(
        "/api/v2/ontologies/{ontology}/actionTypes/{actionType}",
        response_model=ActionTypeV2,
    )
    def get_action_type(
        request: Request, ontology: str, actionType: str
    ) -> ActionTypeV2:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        rec = state.get_action_type(ont.api_name, actionType)
        if rec is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="ActionTypeNotFound",
                parameters={"actionType": actionType},
            )
        return _action_v2(rec)

    @router.get(
        "/api/v2/ontologies/{ontology}/queryTypes",
        response_model=ListQueryTypesResponse,
        response_model_exclude_none=True,
    )
    def list_query_types(
        request: Request,
        ontology: str,
        page_size: int | None = Query(default=None, alias="pageSize"),
        page_token: str | None = Query(default=None, alias="pageToken"),
    ) -> ListQueryTypesResponse:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        items = state.list_query_types(ont.api_name)
        default_ps, max_ps = _page_defaults(request)
        page, token = paginate(
            items,
            page_size=page_size,
            page_token=page_token,
            resource=f"queryTypes:{ont.api_name}",
            codec=_codec(request),
            revision=state.revision,
            default_page_size=default_ps,
            max_page_size=max_ps,
        )
        return ListQueryTypesResponse(
            data=[_query_v2(i) for i in page],
            nextPageToken=token,
        )

    @router.get(
        "/api/v2/ontologies/{ontology}/queryTypes/{queryApiName}",
        response_model=QueryTypeV2,
    )
    def get_query_type(
        request: Request, ontology: str, queryApiName: str
    ) -> QueryTypeV2:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        rec = state.get_query_type(ont.api_name, queryApiName)
        if rec is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="QueryTypeNotFound",
                parameters={"queryApiName": queryApiName},
            )
        return _query_v2(rec)

    @router.post(
        "/api/v2/ontologies/{ontology}/queries/{queryApiName}/execute",
    )
    def execute_query(
        request: Request,
        ontology: str,
        queryApiName: str,
        body: ExecuteQueryRequest,
    ) -> Any:
        state = _state(request)
        ont = _require_ontology(state, ontology)
        rec = state.get_query_type(ont.api_name, queryApiName)
        if rec is None:
            raise FoundryError(
                status_code=404,
                error_code="NOT_FOUND",
                error_name="QueryTypeNotFound",
                parameters={"queryApiName": queryApiName},
            )
        callback = state.query_callbacks.get(queryApiName)
        if callback is not None:
            return callback(body.parameters, state)
        if rec.static_result is not None:
            return rec.static_result
        return {"value": None}

    @router.post(
        "/api/v2/ontologies/{ontology}/actions/{actionType}/apply",
    )
    def apply_action(request: Request, ontology: str, actionType: str) -> None:
        _require_ontology(_state(request), ontology)
        _unsupported(request, "ApplyAction")

    @router.post(
        "/api/v2/ontologies/{ontology}/actions/{actionType}/applyBatch",
    )
    def apply_action_batch(request: Request, ontology: str, actionType: str) -> None:
        _require_ontology(_state(request), ontology)
        _unsupported(request, "ApplyActionBatch")

    return router
