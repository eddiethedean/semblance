# Nested Model Example

Output models with nested structures. Links propagate into nested models.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/nested/app.py)

## Code

```python
"""
Nested model example - output models with nested structures.

Run: semblance run examples.nested.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class Address(BaseModel):
    street: str = ""
    city: Annotated[str, FromInput("city")]
    zip: str = ""


class UserWithAddress(BaseModel):
    name: Annotated[str, FromInput("name")]
    address: Address


class QueryWithCity(BaseModel):
    name: str = "alice"
    city: str = "NYC"


api = SemblanceAPI(seed=42)


@api.get(
    "/user",
    input=QueryWithCity,
    output=UserWithAddress,
    summary="Get user with address",
)
def user():
    """Returns user with nested address; city comes from query."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.nested.app:api --port 8000
```

## Requests and responses

The city is bound to the request. This module uses plain `str` fields for street and ZIP; [the Capper guide](../../docs/guides/realistic-data.md) shows how semantic types improve generated data.

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/user?name=foo&city=Boston'
```

**Output — `200 OK`:**

```json
{
  "name": "foo",
  "address": {
    "street": "HbolMJUevblAbkHClEQa",
    "city": "Boston",
    "zip": "PKriXrefSFPLBYtCRGSE"
  }
}
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/advanced-links.md) for the behavior and available options.
