# Semblance User Guides

Guides for building and testing schema-driven API simulators with Semblance.

## Guides

| Guide | Description |
|-------|-------------|
| [Getting Started](getting-started.md) | Install, first API, and run |
| [Input and Output Binding](input-output-binding.md) | FromInput, DateRangeFrom, query/body/path |
| [Advanced Links](advanced-links.md) | WhenInput, ComputedFrom, nested models |
| [Pagination](pagination.md) | PageParams, PaginatedResponse |
| [Simulation Options](simulation-options.md) | Error rate, latency, rate limiting, filter_by, response validation |
| [Stateful Mode](stateful-mode.md) | POST stores, GET returns stored |
| [CLI](cli.md) | semblance run, export openapi, export fixtures |
| [Plugins](plugins.md) | Custom link types, register_link |
| [Testing](testing.md) | test_client, deterministic seeding, property-based testing, pytest |
| [Foundry adapter](foundry.md) | unofficial ontology-read mock (`semblance-foundry`) |
| [Databricks adapter](databricks.md) | unofficial workspace REST mock (`semblance-databricks`) |
| [Troubleshooting](troubleshooting.md) | common 404/422/429, stateful, and link issues |

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
