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
| [basic](basic/) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](pagination/) | PageParams, PaginatedResponse |
| [nested](nested/) | Nested model linking |
| [stateful](stateful/) | POST stores items, GET returns stored list |
| [advanced](advanced/) | WhenInput, ComputedFrom, filter_by |
