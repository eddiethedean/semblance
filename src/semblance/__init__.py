"""
Semblance --- Schema-driven REST API simulation.

Build fast, realistic API simulators using FastAPI, Pydantic, and Polyfactory
with zero endpoint logic. Behavior is defined by schemas and dependency metadata.
"""

from semblance.api import SemblanceAPI
from semblance.links import DateRangeFrom, FromInput
from semblance.pagination import PageParams, PaginatedResponse
from semblance.testing import test_client

__all__ = [
    "SemblanceAPI",
    "DateRangeFrom",
    "FromInput",
    "PageParams",
    "PaginatedResponse",
    "test_client",
]
