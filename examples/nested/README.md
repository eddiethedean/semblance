# Nested Model Example

Output models with nested structures. Links propagate into nested models.

## Run

```bash
semblance run examples.nested.app:api --port 8000
```

## Try

```bash
curl "http://127.0.0.1:8000/user?name=foo&city=Boston"
```

## Concepts

- **Nested models** – `UserWithAddress` contains `Address`
- **Links in nested fields** – `city` in `Address` uses `FromInput("city")`
- Resolver traverses nested models to apply links
