# Getting Started

This guide walks you through creating your first Semblance API in under five minutes.

## Install

```bash
pip install semblance
```

Requires Python 3.10+.

## Your First API

Create a file `app.py`:

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

## Run It

```bash
uvicorn app:app --reload
```

## Try It

```bash
curl "http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31"
```

Example response:

```json
[
  {"name": "alice", "created_at": "2024-08-21T09:22:43.516168"},
  {"name": "alice", "created_at": "2024-01-10T03:05:39.176702"}
]
```

Each user's `name` comes from the query (`alice`), and `created_at` is a random datetime in the date range.

## How It Works

1. **Input model** (`UserQuery`) – validates the request (query params, body, or path).
2. **Output model** (`User`) – defines the response shape.
3. **Links** (`FromInput`, `DateRangeFrom`) – declare how output fields relate to input. No endpoint logic required.

The handler body is empty; Semblance generates responses from your schemas.

## Next Steps

- [Input and Output Binding](input-output-binding.md) – bind fields from input, date ranges, and more
- [Testing](testing.md) – use the test client with pytest
