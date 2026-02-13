# Stateful Example

POST creates and stores items; GET list returns stored instances.

## Run

```bash
semblance run examples.stateful.app:api --port 8000
```

## Try

```bash
# Create users
curl -X POST "http://127.0.0.1:8000/users" -H "Content-Type: application/json" -d '{"name":"alice"}'
curl -X POST "http://127.0.0.1:8000/users" -H "Content-Type: application/json" -d '{"name":"bob"}'

# List stored users
curl "http://127.0.0.1:8000/users?name=x"
```

## Concepts

- **stateful=True** – SemblanceAPI stores POST responses
- **GET list** – returns stored instances, not newly generated
- **id** – auto-generated for models with id field
- State is process-local (in-memory)
