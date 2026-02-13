# Pagination Example

List endpoint with `PageParams` and `PaginatedResponse`.

## Run

```bash
semblance run examples.pagination.app:api --port 8000
```

## Try

```bash
curl "http://127.0.0.1:8000/users?limit=5&offset=0&name=alice"
curl "http://127.0.0.1:8000/users?limit=3&offset=10"
```

## Concepts

- **PageParams** – `limit` and `offset` query params
- **PaginatedResponse[T]** – `items`, `total`, `limit`, `offset`
- **list_count="limit"** – use input `limit` for list length
