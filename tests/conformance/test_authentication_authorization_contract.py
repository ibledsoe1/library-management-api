"""Conformance tests for the documented security contract."""

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


@pytest.mark.parametrize(
    ("path", "method", "expected_statuses"),
    [
        ("/members", "get", {"200", "401"}),
        ("/members", "post", {"201", "401", "403", "409", "422"}),
        ("/members/{member_id}", "get", {"200", "401", "404", "422"}),
        ("/members/{member_id}", "put", {"200", "401", "403", "404", "409", "422"}),
        ("/members/{member_id}", "delete", {"204", "401", "403", "404", "409", "422"}),
        ("/members/{member_id}/books", "get", {"200", "401", "404", "422"}),
        ("/books", "get", {"200", "401"}),
        ("/books", "post", {"201", "401", "403", "404", "409", "422"}),
        ("/books/{book_id}", "get", {"200", "401", "404", "422"}),
        ("/books/{book_id}", "put", {"200", "401", "403", "404", "409", "422"}),
        ("/books/{book_id}", "delete", {"204", "401", "403", "404", "422"}),
    ],
)
def test_openapi_marks_resource_operations_as_bearer_protected(
    database_client: TestClient,
    path: str,
    method: str,
    expected_statuses: set[str],
) -> None:
    """Every resource operation publishes Bearer security and expected outcomes."""
    operation = database_client.get("/openapi.json").json()["paths"][path][method]

    assert operation["security"] == [{"BearerAuthentication": []}]
    assert expected_statuses <= set(operation["responses"])


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/members", "post"),
        ("/members/{member_id}", "put"),
        ("/members/{member_id}", "delete"),
        ("/books", "post"),
        ("/books/{book_id}", "put"),
        ("/books/{book_id}", "delete"),
    ],
)
def test_openapi_documents_401_and_403_for_administrator_writes(
    database_client: TestClient,
    path: str,
    method: str,
) -> None:
    """Write operations document the Bearer challenge and the role denial."""
    responses = database_client.get("/openapi.json").json()["paths"][path][method][
        "responses"
    ]

    assert "WWW-Authenticate" in responses["401"]["headers"]
    assert responses["403"]["description"]


@pytest.mark.parametrize(
    ("path", "method"),
    [("/", "get"), ("/health", "get")],
)
def test_openapi_leaves_public_operations_without_security(
    database_client: TestClient,
    path: str,
    method: str,
) -> None:
    """Root and health do not publish a security requirement."""
    operation = database_client.get("/openapi.json").json()["paths"][path][method]

    assert "security" not in operation