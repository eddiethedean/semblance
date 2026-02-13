# Plugins Example

Custom link type (`FromEnv`) that reads values from environment variables.

## Code

```python
"""
Plugins example - custom link (FromEnv).

Set USER_NAME env var to override the default:
  USER_NAME=Bob semblance run examples.plugins.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI, register_link


class FromEnv:
    """Custom link: read value from environment variable."""

    def __init__(self, env_var: str):
        self.env_var = env_var

    def resolve(self, input_data: dict, rng):
        import os
        return os.environ.get(self.env_var)


register_link(FromEnv)


class User(BaseModel):
    name: Annotated[str, FromEnv("USER_NAME")]
    role: Annotated[str, FromInput("role")]


class UserQuery(BaseModel):
    role: str = "viewer"


api = SemblanceAPI(seed=42)


@api.get(
    "/user",
    input=UserQuery,
    output=User,
    summary="Get user (name from USER_NAME env)",
)
def user():
    """name comes from USER_NAME env; role from query."""
    pass


app = api.as_fastapi()
```

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

*Without `USER_NAME`, Polyfactory generates the name (values vary per run).*

## Concepts

- **register_link** – register custom link class
- **resolve(input_data, rng)** – return override value or `None` for Polyfactory
- Use for env-based config, feature flags, or custom binding logic
