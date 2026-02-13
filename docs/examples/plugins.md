# Plugins Example

Custom link type (`FromEnv`) that reads values from environment variables.

## Run

```bash
# Default: USER_NAME not set, Polyfactory generates name
semblance run examples.plugins.app:api --port 8000

# Override: name from env
USER_NAME=Bob semblance run examples.plugins.app:api --port 8000
```

## Try

```bash
# Without USER_NAME set
curl "http://127.0.0.1:8000/user?role=admin"
# → {"name": "<generated>", "role": "admin"}

# With USER_NAME=DocBot (before starting server)
USER_NAME=DocBot semblance run examples.plugins.app:api --port 8000
# In another terminal:
curl "http://127.0.0.1:8000/user?role=admin"
# → {"name": "DocBot", "role": "admin"}
```

Example output with `USER_NAME=DocBot`:

```json
{"name": "DocBot", "role": "admin"}
```

## Concepts

- **register_link** – register custom link class
- **resolve(input_data, rng)** – return override value or `None` for Polyfactory
- Use for env-based config, feature flags, or custom binding logic
