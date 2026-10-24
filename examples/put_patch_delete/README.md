# PUT, PATCH, DELETE Example

Demonstrates non-stateful PUT, PATCH, and DELETE endpoints. Responses are generated from schemas; no persistence.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/put_patch_delete/app.py)

## Code

```python
"""
Phase 5 example: PUT, PATCH, DELETE endpoints (non-stateful).

Run: semblance run examples.put_patch_delete.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class User(BaseModel):
    """Output model for user resources."""

    id: str = ""
    name: Annotated[str, FromInput("name")]


class UpdateBody(BaseModel):
    """Request body for PUT and PATCH."""

    name: str = "updated"


class PathIdInput(BaseModel):
    """Path parameter for by-id routes."""

    id: str = ""


api = SemblanceAPI(seed=42)


@api.put("/users/{id}", input=UpdateBody, output=User, summary="Replace user")
def put_user():
    """PUT returns a generated response; path param id is available for links."""
    pass


@api.patch("/users/{id}", input=UpdateBody, output=User, summary="Update user")
def patch_user():
    """PATCH returns a generated response with body merged into path params."""
    pass


@api.delete("/users/{id}", input=PathIdInput, summary="Delete user")
def delete_user():
    """DELETE with no output returns 204 No Content."""
    pass


@api.delete(
    "/users/{id}/with-body",
    input=PathIdInput,
    output=User,
    summary="Delete user (return deleted)",
)
def delete_user_with_output():
    """DELETE with output returns 200 and a generated body."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.put_patch_delete.app:api --port 8000
```

## Requests and responses

These routes generate responses without storing them. The output `id` is a generated string, so it does not echo the path ID.

**Input 1:**

```bash
curl -sS -X PUT http://127.0.0.1:8000/users/abc -H 'Content-Type: application/json' -d '{"name": "put-user"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "put-user"}
```

**Input 2:**

```bash
curl -sS -X PATCH http://127.0.0.1:8000/users/xyz -H 'Content-Type: application/json' -d '{"name": "patch-user"}'
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "patch-user"}
```

**Input 3:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/123
```

**Output — `204 No Content`:**

No response body.

**Input 4:**

```bash
curl -sS -X DELETE http://127.0.0.1:8000/users/123/with-body
```

**Output — `200 OK`:**

```json
{"id": "HbolMJUevblAbkHClEQa", "name": "PKriXrefSFPLBYtCRGSE"}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/input-output-binding.md) for the behavior and available options.
