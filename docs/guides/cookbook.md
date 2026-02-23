# Cookbook

Short recipes for common tasks. Each links to the full guide or example.

## Pagination

Use `PageParams` in your input model and `PaginatedResponse[Model]` as the output type:

```python
from semblance import PageParams, PaginatedResponse

class UserListQuery(PageParams, BaseModel):
    name: str = "alice"

@api.get("/users", input=UserListQuery, output=PaginatedResponse[User])
def users():
    pass
```

See [Pagination](pagination.md) and the [pagination example](../examples/pagination.md).

## Stateful CRUD

Enable stateful mode and register POST, GET list, GET by id, PUT, PATCH, DELETE:

```python
api = SemblanceAPI(stateful=True)
api.post("/users", input=CreateUser, output=UserWithId)(...)
api.get("/users", input=..., output=list[UserWithId])(...)
api.get("/users/{id}", input=PathIdInput, output=UserWithId)(...)
api.put("/users/{id}", input=UpdateBody, output=UserWithId)(...)
api.patch("/users/{id}", input=UpdateBody, output=UserWithId)(...)
api.delete("/users/{id}", input=PathIdInput)(...)
```

See [Stateful Mode](stateful-mode.md) and the [stateful CRUD example](../examples/stateful_crud.md).

## Request links (headers and cookies)

Bind output fields to the current request:

```python
from semblance import FromHeader, FromCookie

class Out(BaseModel):
    request_id: Annotated[str, FromHeader("X-Request-Id")]
    session: Annotated[str, FromCookie("session_id")]
```

See [Request Links](request-links.md) and the [request links example](../examples/request_links.md).

## Rate limiting

Return 429 when the endpoint is hit too often:

```python
@api.get("/users", input=Query, output=list[User], rate_limit=10)
def users():
    pass
```

See [Simulation Options](simulation-options.md).

## Property-based testing

Use Hypothesis with Semblance’s helpers to generate inputs and assert on responses:

```python
from semblance.property_testing import strategy_for_input_model, test_endpoint

@given(data=st.data())
def test_users(data):
    test_endpoint(data, client, "GET", "/users", UserQuery, list[User])
```

See [Testing](testing.md).
