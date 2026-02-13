# Semblance Examples

Curated, runnable examples for common use cases.

## Running Examples

From the project root (with semblance installed):

```bash
semblance run examples.<name>.app:api --port 8000
```

Or with uvicorn:

```bash
uvicorn examples.<name>.app:app --reload
```

## Examples

| Example | Description |
|---------|-------------|
| [basic](basic.md) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](pagination.md) | PageParams, PaginatedResponse |
| [nested](nested.md) | Nested model linking |
| [stateful](stateful.md) | POST stores items, GET returns stored list |
| [advanced](advanced.md) | WhenInput, ComputedFrom, filter_by |
| [error_simulation](error_simulation.md) | error_rate, error_codes |
| [plugins](plugins.md) | Custom link (FromEnv) |
