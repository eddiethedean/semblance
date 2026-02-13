# Semblance Examples

Curated, runnable examples for common use cases.

## Running Examples

From the project root (with semblance installed: `pip install -e .`):

```bash
# CLI (recommended)
semblance run examples.<name>.app:api --port 8000

# Or with uvicorn
uvicorn examples.<name>.app:app --reload

# Or run the app module directly
python examples/basic/app.py
```

## Examples

| Example | Description |
|---------|-------------|
| [basic](basic/) | Minimal GET list with FromInput, DateRangeFrom |
| [pagination](pagination/) | PageParams, PaginatedResponse |
| [nested](nested/) | Nested model linking |
| [stateful](stateful/) | POST stores items, GET returns stored list |
| [advanced](advanced/) | WhenInput, ComputedFrom, filter_by |
