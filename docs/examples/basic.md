# Basic Example

Minimal Semblance API with a single GET list endpoint.

## Run

```bash
semblance run examples.basic.app:api --port 8000
# or
uvicorn examples.basic.app:app --reload
```

## Try

```bash
curl "http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31"
```

Example response:

```json
[
  {"name": "alice", "created_at": "2024-08-21T09:22:43.516168"},
  {"name": "alice", "created_at": "2024-01-10T03:05:39.176702"}
]
```

*Values vary per run. Use `SemblanceAPI(seed=42)` for reproducible output.*

## Concepts

- **UserQuery** – input model for query params
- **User** – output model with `FromInput` and `DateRangeFrom` links
- No endpoint logic – schemas drive behavior
