# Advanced Links

This guide covers conditional dependencies, cross-field constraints, and nested model linking.

## WhenInput

Apply a link only when an input condition is met:

```python
from typing import Annotated
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
    placed_at: Annotated[datetime, DateRangeFrom("start", "end")]
    total_display: Annotated[str, ComputedFrom(("subtotal",), lambda s: f"${s:.2f}")]
```
