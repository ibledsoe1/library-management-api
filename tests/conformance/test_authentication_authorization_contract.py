"""Conformance tests for the documented security contract."""

from typing import Any

import pytest
from starlette.testclient import TestClient

# OPENAPI SECURITY SCHEME
# HTTPBearer adds the reusable scheme to OpenAPI. The protected route
# dependencies add a security requirement to each resource operation.


def test_openapi_declares_the_bearer_authentication_scheme(
    database_client: TestClient,
) -> None:
    """API clients can discover the Bearer scheme from the public contract."""
    document = database_client.get("/openapi.json").json()
    scheme = document["components"]["securitySchemes"]["BearerAuthentication"]

    assert scheme["type"] == "http"
    assert scheme["scheme"] == "bearer"

# TODO: edit these to match extra stuff in library management API
@pytest.mark.parametrize(
    ("path", "method", "expected_statuses"),
    [
        ("/members", "get", {"200", "401", "422"}),
        ("/members", "post", {"201", "401", "403", "409", "422"}),
        ("/members/{member_id}", "put", {"200", "401", "403", "404", "409", "422"}),
        ("/books", "get", {"200", "401", "422"}), 
        ("/books", "post", {"201", "401", "403", "404", "409", "422"}),
        ("/books/{book_id}", "delete", {"204", "401", "403", "404", "422"}),
    ],
)
def test_openapi_marks_resource_operations_as_bearer_protected(
    database_client: TestClient,
    path: str,
    method: str,
    expected_statuses: set[str],
) -> None:
    """Representative operations publish Bearer security and expected outcomes."""
    operation = database_client.get("/openapi.json").json()["paths"][path][method]

    assert operation["security"] == [{"BearerAuthentication": []}]
    assert expected_statuses <= set(operation["responses"])