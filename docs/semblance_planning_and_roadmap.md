# Semblance --- Schema-Driven API Simulation

## 1. Project Overview

**Semblance** is a Python package for building fast, realistic REST API
simulators using **FastAPI**, **Pydantic**, and **Polyfactory**.

Semblance allows developers to define API behavior declaratively using
schemas alone. Input models, output models, and relationships between
them fully determine API responses, with no endpoint logic required.

> *A semblance is the appearance or form of something --- not the thing
> itself.*\
> Semblance creates APIs that look and behave real enough to test,
> prototype, and integrate against.

------------------------------------------------------------------------

## 2. Core Goals

-   Zero endpoint logic
-   Schema-driven behavior
-   Deterministic but randomized responses
-   FastAPI-native developer experience
-   First-class testing support
-   Extensible dependency/constraint system

Non-goals: - Business logic execution - Database simulation - Full
backend replacement

------------------------------------------------------------------------

## 3. Core Concepts

### 3.1 Schema as Behavior

Semblance treats Pydantic models as executable contracts.

-   Input models describe *requests*
-   Output models describe *responses*
-   Metadata describes *relationships*

No imperative glue code is required.

------------------------------------------------------------------------

### 3.2 Model-Embedded Dependencies

Relationships are declared inside output models using `typing.Annotated`
metadata.

``` python
@dataclass(frozen=True)
class FromInput:
    field: str

@dataclass(frozen=True)
class DateRangeFrom:
    start: str
    end: str
```

``` python
class UserQuery(BaseModel):
    name: str
    start_date: date
    end_date: date

class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date")
    ]
```

Dependencies live with the fields they affect.

------------------------------------------------------------------------

## 4. High-Level Architecture

### Request Lifecycle

1.  Request received by FastAPI
2.  Input model validated
3.  Output model inspected for dependency metadata
4.  Dependency resolver builds generation strategies
5.  Polyfactory generates response objects
6.  Response returned

### Key Components

-   `semblance.api` --- endpoint registration & app creation
-   `semblance.links` --- dependency metadata & DSL
-   `semblance.resolver` --- constraint resolution engine
-   `semblance.factory` --- Polyfactory integration layer
-   `semblance.testing` --- pytest utilities

------------------------------------------------------------------------

## 5. Public API (Proposed)

``` python
from semblance import SemblanceAPI

api = SemblanceAPI()

@api.get(
    "/users",
    input=UserQuery,
    output=list[User],
)
def users():
    pass

app = api.as_fastapi()
```

Endpoint bodies are optional and ignored.

------------------------------------------------------------------------

## 6. Dependency Resolution Model

-   Dependencies resolve to **generation strategies**, not values
-   Strategies are translated into Polyfactory overrides
-   Supports:
    -   Static bindings
    -   Callable generators
    -   Collection-wide constraints

Example resolved override:

``` python
{
    "name": input.name,
    "created_at": lambda: random_datetime(start, end)
}
```

------------------------------------------------------------------------

## 7. Testing & Tooling

### Pytest Harness

``` python
@pytest.fixture
def client():
    return semblance.test_client()
```

Supports: - Contract testing - Snapshot testing - Frontend-backend
integration tests

------------------------------------------------------------------------

## 8. Roadmap

### Phase 1 --- MVP (Foundations)

**Goal:** Usable, minimal, stable

-   [x] SemblanceAPI core
-   [x] GET endpoints
-   [x] Query parameter inputs
-   [x] Single & list outputs
-   [x] `FromInput` binding
-   [x] `DateRangeFrom` constraint
-   [x] Polyfactory integration
-   [x] FastAPI app export
-   [x] Basic pytest client

------------------------------------------------------------------------

### Phase 2 --- Practical Expansion

**Goal:** Real-world testing usefulness

-   [x] POST endpoints with body models
-   [x] Path parameter support
-   [x] Pagination helpers
-   [x] Deterministic seeding
-   [x] Error response simulation
-   [x] Response count / limit constraints

------------------------------------------------------------------------

### Phase 3 --- Advanced Simulation

**Goal:** Expressive behavior modeling

-   [ ] Conditional dependencies
-   [ ] Cross-field constraints
-   [ ] Collection filtering constraints
-   [ ] Nested model linking
-   [ ] Optional stateful mode (opt-in)
-   [ ] Latency & jitter simulation

------------------------------------------------------------------------

### Phase 4 --- Ecosystem & Polish

**Goal:** Adoption and extensibility

-   [ ] Plugin system for custom links
-   [ ] OpenAPI schema annotations
-   [ ] CLI runner
-   [ ] Frontend mock export
-   [ ] Documentation site
-   [ ] Example galleries

------------------------------------------------------------------------

## 9. Risks & Design Guardrails

-   Avoid model-to-model imports to prevent coupling
-   Keep dependency DSL explicit and inspectable
-   Prefer composition over magic
-   Maintain FastAPI and Pydantic idioms

------------------------------------------------------------------------

## 10. Summary

Semblance provides a clean, declarative way to create realistic API
simulations using schemas alone. By embedding behavioral constraints
directly into Pydantic models, Semblance enables fast, reliable testing
and prototyping without sacrificing correctness or developer ergonomics.
