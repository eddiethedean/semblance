"""
Semblance --- Schema-driven REST API simulation.

Build fast, realistic API simulators using FastAPI, Pydantic, and Polyfactory
with zero endpoint logic. Behavior is defined by schemas and link metadata
(FromInput, DateRangeFrom, WhenInput, ComputedFrom, or custom via register_link).
"""

from semblance.api import SemblanceAPI
from semblance.errors import ErrorCase, ScenarioStep
from semblance.links import (
    ComputedFrom,
    DateRangeFrom,
    FromCookie,
    FromHeader,
    FromInput,
    FromJsonFixture,
    FromNestedFixture,
    WhenInput,
)
from semblance.pagination import PageParams, PageSlice, PageTable, PaginatedResponse
from semblance.plugins import LinkProtocol, register_link
from semblance.testing import test_client

__all__ = [
    "ComputedFrom",
    "DateRangeFrom",
    "ErrorCase",
    "FromCookie",
    "FromHeader",
    "FromInput",
    "FromJsonFixture",
    "FromNestedFixture",
    "LinkProtocol",
    "PageParams",
    "PageSlice",
    "PageTable",
    "PaginatedResponse",
    "register_link",
    "ScenarioStep",
    "SemblanceAPI",
    "test_client",
    "WhenInput",
]
