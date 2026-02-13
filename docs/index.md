# Semblance

**Schema-driven REST API simulation** with FastAPI, Pydantic, and Polyfactory.

Semblance lets you define API behavior declaratively using schemas alone. Input models, output models, and relationships between them fully determine API responses — **no endpoint logic required**.

> *A semblance is the appearance or form of something — not the thing itself.*  
> Semblance creates APIs that look and behave real enough to test, prototype, and integrate against.

## Quick Start

```bash
pip install semblance
```

Create `app.py`:

```python
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel
from semblance import DateRangeFrom, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]


api = SemblanceAPI()


@api.get("/users", input=UserQuery, output=list[User])
def users():
    pass


app = api.as_fastapi()
```

Run:

```bash
semblance run app:api --port 8000
# or
uvicorn app:app --reload
```

Try:

```bash
curl "http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31"
```

## Features

- **Zero endpoint logic** — schemas drive behavior
- **Schema-driven** — input/output models and links define responses
- **Deterministic seeding** — reproducible responses for tests
- **FastAPI-native** — full OpenAPI, validation, async
- **Extensible** — custom link types via plugins

## Next Steps

- [Getting Started](guides/getting-started.md) — full walkthrough
- [Input and Output Binding](guides/input-output-binding.md) — FromInput, DateRangeFrom, and more
- [Examples](examples/README.md) — runnable examples
- [API Reference](api/index.md) — module reference
