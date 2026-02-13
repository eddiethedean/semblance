# Semblance User Guides

Guides for building and testing schema-driven API simulators with Semblance.

## Guides

| Guide | Description |
|-------|-------------|
| [Getting Started](getting-started.md) | Install, first API, and run |
| [Input and Output Binding](input-output-binding.md) | FromInput, DateRangeFrom, query/body/path |
| [Advanced Links](advanced-links.md) | WhenInput, ComputedFrom, nested models |
| [Pagination](pagination.md) | PageParams, PaginatedResponse |
| [Testing](testing.md) | test_client, deterministic seeding, pytest |
| [Simulation Options](simulation-options.md) | Error rate, latency, filter_by |
| [Stateful Mode](stateful-mode.md) | POST stores, GET returns stored |

## Quick Reference

```python
from semblance import (
    ComputedFrom,
    DateRangeFrom,
    FromInput,
    PageParams,
    PaginatedResponse,
    SemblanceAPI,
    WhenInput,
    test_client,
)
```
