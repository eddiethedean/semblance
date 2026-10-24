# Advanced Links

This guide covers conditional dependencies, cross-field constraints, and nested model linking.

These snippets show output model definitions to use in an existing app. See the [advanced example](../examples/advanced.md) for complete input models, routes, and requests.

## WhenInput

Apply a link only when an input condition is met:

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromInput, WhenInput

class UserWithStatus(BaseModel):
    name: Annotated[str, FromInput("name")]
    status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]
```

When `include_status` is `True`, `status` is bound from input. Otherwise Polyfactory generates it.

Example (`GET /user?name=x&status=admin&include_status=true`):

```json
{"name": "x", "status": "admin"}
```

## ComputedFrom

Compute an output field from other output fields in the same model:

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import ComputedFrom, FromInput

class UserWithFullName(BaseModel):
    first: Annotated[str, FromInput("first")]
    last: Annotated[str, FromInput("last")]
    full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]
```

Dependency fields must be resolved first (e.g. via `FromInput` or other links). Semblance evaluates in dependency order.

Example (`GET /user?first=Jane&last=Smith`):

```json
{"first": "Jane", "last": "Smith", "full": "Jane Smith"}
```

## Nested Model Linking

Links work inside nested models. Define a nested model with its own links:

```python
class Address(BaseModel):
    city: Annotated[str, FromInput("city")]

class UserWithAddress(BaseModel):
    name: Annotated[str, FromInput("name")]
    address: Address
```

Request `GET /user?name=alice&city=Boston` – the response `address.city` will be `"Boston"`:

```json
{"name": "alice", "address": {"city": "Boston"}}
```

## Combining Links

You can mix links on different fields:

```python
class Order(BaseModel):
    customer: Annotated[str, FromInput("customer_id")]
    subtotal: float
    placed_at: Annotated[datetime, DateRangeFrom("start", "end")]
    total_display: Annotated[str, ComputedFrom(("subtotal",), lambda s: f"${s:.2f}")]
```

## JSON fixture links

Load values from a JSON file. Pointers are slash paths (`items/0/name`). `variant_from` plus `variants` picks an alternate pointer from an input field. Default miss skips the override (Polyfactory fills the field). `strict=True` returns 500 `Fixture miss`.

```python
from typing import Annotated
from pydantic import BaseModel
from semblance import FromJsonFixture, FromNestedFixture

class FileRow(BaseModel):
    title: Annotated[str, FromJsonFixture("data.json", pointer="pages/first/0/title")]

class PersonOut(BaseModel):
    person: Annotated[
        FileRow,
        FromNestedFixture(
            "data.json",
            pointer="people",
            where={"office": "office"},
        ),
    ]
```

`FromNestedFixture` walks a list: `index` picks a position; `where` maps object field → input field and takes the first match.
