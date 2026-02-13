"""
Semblance --- Schema-driven REST API simulation.

Build fast, realistic API simulators using FastAPI, Pydantic, and Polyfactory
with zero endpoint logic. Behavior is defined by schemas and dependency metadata.
"""

from semblance.api import SemblanceAPI
from semblance.links import ComputedFrom, DateRangeFrom, FromInput, WhenInput
from semblance.pagination import PageParams, PaginatedResponse
from semblance.testing import test_client

__all__ = [
    "ComputedFrom",
    "SemblanceAPI",
    "DateRangeFrom",
    "FromInput",
    "PageParams",
    "PaginatedResponse",
    "test_client",
    "WhenInput",
]
