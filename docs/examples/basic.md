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

## Concepts

- **UserQuery** – input model for query params
- **User** – output model with `FromInput` and `DateRangeFrom` links
- No endpoint logic – schemas drive behavior
