# Realistic data with Capper

Use [Capper](https://github.com/eddiethedean/capper) semantic types to generate names, emails, companies, and cities. Capper integrates with Polyfactory, so you can use its types directly in Semblance output models.

## Install

Capper is optional. Install its Pydantic integration alongside Semblance:

```bash
pip install semblance "capper[pydantic]"
```

## Define a customer

Save this as **`realistic.py`**:

```python
from typing import Annotated

from capper import City, Company, Email, Name
from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class CustomerQuery(BaseModel):
    segment: str = "trial"
    seed: int = 42


class Customer(BaseModel):
    name: Name
    email: Email
    company: Company
    city: City
    segment: Annotated[str, FromInput("segment")]


api = SemblanceAPI()


@api.get("/customer", input=CustomerQuery, output=Customer, seed_from="seed")
def customer():
    pass
```

`FromInput` supplies the requested segment. Capper's types select Faker providers for the other fields. No custom factory registration is required.

## Run and request

```bash
semblance run realistic:api --port 8002
```

In another terminal:

```bash
curl "http://127.0.0.1:8002/customer?segment=enterprise&seed=42"
```

**Output — `200 OK`:**

```json
{
  "name": "Allison Hill",
  "email": "donaldgarcia@example.net",
  "company": "Miller, Henderson and Johnson",
  "city": "East William",
  "segment": "enterprise"
}
```

This response was captured with Capper 1.1.1, Faker 40.43.0, and Polyfactory 3.5.0. Generated values can change after dependency upgrades.

## Make a customer repeatable

The route reads its seed from the `seed` input field. Repeat the request with `seed=42` for the same generated values with the same installed dependencies. Change the seed to generate another customer.

Leave the API constructor unseeded when you want `seed_from="seed"` to control generation. A global seed such as `SemblanceAPI(seed=42)` takes precedence over request seeds.

## Keep related fields consistent

Capper generates each field independently. The example email does not derive from the generated name, and the city does not describe the company's address. Use [ComputedFrom](advanced-links.md#computedfrom) for fields that depend on other output fields, [fixture links](advanced-links.md#json-fixture-links) for curated records, or [custom links](plugins.md) for domain-specific generation.

For example, replace the `Customer` definition with this model, adding the import above it:

```python
from semblance import ComputedFrom


class Customer(BaseModel):
    name: Name
    email: Email
    company: Company
    city: City
    segment: Annotated[str, FromInput("segment")]
    display: Annotated[
        str,
        ComputedFrom(("name", "company"), lambda name, company: f"{name} at {company}"),
    ]
```

The `display` field is computed from that response's generated name and company. See [Testing](testing.md) for assertions that check relationships as well as response shape.
