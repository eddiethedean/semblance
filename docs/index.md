# Semblance

**Build a REST API simulator from Pydantic models.**

Semblance turns request and response schemas into a running FastAPI app. Bind response fields to request data, generate realistic values, keep state across requests, and exercise a client's retry behavior without writing endpoint logic.

[Get started](guides/getting-started.md){ .md-button .md-button--primary }
[Explore the examples](examples/README.md){ .md-button }

## A working API in one file

Requires **Python 3.10+**. FastAPI, Pydantic, Polyfactory, and Uvicorn are installed with Semblance.

```bash
pip install semblance
```

Save this as `app.py`:

```python
from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI(seed=42)


@api.get("/users", input=UserQuery, output=list[User], list_count=2)
def users():
    pass


app = api.as_fastapi()
```

Start the API:

```bash
semblance run app:api --port 8000
```

In another terminal, send a request:

```bash
curl "http://127.0.0.1:8000/users?name=alice"
```

The response is **`200 OK`**:

```json
[{"name": "alice"}, {"name": "alice"}]
```

Open [localhost:8000/docs](http://127.0.0.1:8000/docs) to try the API interactively. FastAPI serves the generated schema at `/openapi.json`.

## How responses are built

1. The **input model** validates query parameters, path parameters, or the JSON body.
2. The **output model** defines the response shape. Polyfactory generates fields, and `Annotated` links supply values from requests, other output fields, or fixtures.
3. **Route options** control list size, pagination, errors, timing, and authentication.

The decorated function registers the route. Its body is a placeholder; Semblance generates responses from the models and route options.

## Choose your next step

| You want to… | Start here |
|---|---|
| Build your first simulator | [Getting started](guides/getting-started.md) |
| Generate names, emails, companies, and cities | [Realistic data with Capper](guides/realistic-data.md) |
| Bind responses to inputs or other fields | [Input and output binding](guides/input-output-binding.md), [advanced links](guides/advanced-links.md) |
| Keep created resources between requests | [Stateful mode](guides/stateful-mode.md) |
| Test retries, errors, latency, or rate limits | [Simulation options](guides/simulation-options.md) |
| Test a client without starting a server | [Testing](guides/testing.md) |
| Browse working requests and responses | [Examples](examples/README.md) |
| Look up an option | [API reference](api/index.md), [CLI](guides/cli.md) |

## Adapter packages

Install adapters separately when your client expects a particular external API. Each adapter documents its supported operations and limitations.

| Package | Simulated API | Guide |
|---|---|---|
| `semblance-foundry` | Selected Foundry API v2 ontology operations | [Foundry adapter](guides/foundry.md) |
| `semblance-databricks` | Selected Databricks workspace REST operations | [Databricks adapter](guides/databricks.md) |

## Project resources

[Source code](https://github.com/eddiethedean/semblance) · [Changelog](https://github.com/eddiethedean/semblance/blob/main/CHANGELOG.md) · [Contributing](https://github.com/eddiethedean/semblance/blob/main/CONTRIBUTING.md) · [Report an issue](https://github.com/eddiethedean/semblance/issues)
