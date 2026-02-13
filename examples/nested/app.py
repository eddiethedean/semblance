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


api = SemblanceAPI()


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
