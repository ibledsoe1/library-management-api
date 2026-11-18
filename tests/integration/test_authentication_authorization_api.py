"""Integration tests for authentication and role-based authorization."""

import pytest
from starlette.testclient import TestClient


# PUBLIC AND AUTHENTICATED READS
# Root and health remain public. Resource reads require a valid token, and both
# roles may perform them.


def test_root_and_health_remain_public(database_client: TestClient) -> None:
    """The introductory endpoints do not require a Bearer token."""
    assert database_client.get("/").status_code == 200
    assert database_client.get("/health").status_code == 200


def test_docs_endpoints_remain_public(database_client: TestClient) -> None:
    """The OpenAPI document and Swagger UI can be opened without a token."""
    assert database_client.get("/openapi.json").status_code == 200
    assert database_client.get("/docs").status_code == 200
    assert database_client.get("/redoc").status_code == 200


def test_protected_read_rejects_a_missing_token(database_client: TestClient) -> None:
    """A missing Bearer token receives 401 and the standard challenge header."""
    response = database_client.get("/members")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid Bearer token"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_read_rejects_an_unknown_token(database_client: TestClient) -> None:
    """An unrecognized Bearer token is not treated as an authenticated user."""
    response = database_client.get(
        "/books",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_read_rejects_a_malformed_authorization_header(
    database_client: TestClient,
) -> None:
    """A non-Bearer scheme is rejected with the same 401 challenge."""
    response = database_client.get(
        "/members",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("path", ["/members", "/books"])
def test_member_can_read_protected_collections(
    database_client: TestClient,
    member_headers: dict[str, str],
    path: str,
) -> None:
    """A member token permits safe resource reads."""
    response = database_client.get(path, headers=member_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("path", ["/members", "/books"])
def test_administrator_can_read_protected_collections(
    database_client: TestClient,
    admin_headers: dict[str, str],
    path: str,
) -> None:
    """An administrator token also permits resource reads."""
    response = database_client.get(path, headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == []


# ADMINISTRATOR-ONLY WRITES
# A member is authenticated but lacks the administrator role, so write routes
# return 403 before reaching request validation or the service layer.

VALID_MEMBER_BODY = {
    "name": "Denied Member",
    "email": "denied.member@collin.edu",
    "membership_id": "DENIED-1",
    "phone": "1234567890",
}
VALID_BOOK_BODY = {
    "title": "Denied Book",
    "author": "Denied Author",
    "isbn": "978-7777777777",
    "published_year": 2000,
    "member_id": 999999,
}


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/members", VALID_MEMBER_BODY),
        ("PUT", "/members/999999", VALID_MEMBER_BODY),
        ("DELETE", "/members/999999", None),
        ("POST", "/books", VALID_BOOK_BODY),
        ("PUT", "/books/999999", VALID_BOOK_BODY),
        ("DELETE", "/books/999999", None),
    ],
)
def test_member_cannot_use_administrator_only_write_routes(
    database_client: TestClient,
    member_headers: dict[str, str],
    method: str,
    path: str,
    json_body: dict[str, object] | None,
) -> None:
    """Every Member and Book write operation requires the administrator role."""
    response = database_client.request(
        method,
        path,
        json=json_body,
        headers=member_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Administrator role required"}


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/members", VALID_MEMBER_BODY),
        ("DELETE", "/members/999999", None),
        ("POST", "/books", VALID_BOOK_BODY),
    ],
)
def test_unauthenticated_write_routes_return_401(
    database_client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, object] | None,
) -> None:
    """A write without any token is rejected as unauthenticated, not forbidden."""
    response = database_client.request(method, path, json=json_body)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_denied_member_write_does_not_change_library_data(
    database_client: TestClient,
    member_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    """A 403 write must leave stored Members untouched."""
    denied = database_client.post(
        "/members", json=VALID_MEMBER_BODY, headers=member_headers
    )

    assert denied.status_code == 403
    assert database_client.get("/members", headers=admin_headers).json() == []


def test_administrator_can_complete_a_member_and_book_write_workflow(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """An admin token reaches the existing CRUD workflow after authorization."""
    member_response = database_client.post(
        "/members",
        json={
            "name": "Authorized Member",
            "email": "authorized.member@collin.edu",
            "membership_id": "AUTH-1",
            "phone": "1234567890",
        },
        headers=admin_headers,
    )
    assert member_response.status_code == 201
    member = member_response.json()

    book_response = database_client.post(
        "/books",
        json={
            "title": "Authorized Book",
            "author": "Authorized Author",
            "isbn": "978-8888888888",
            "published_year": 2000,
            "member_id": member["id"],
        },
        headers=admin_headers,
    )
    assert book_response.status_code == 201
    book = book_response.json()

    replace_response = database_client.put(
        f"/books/{book['id']}",
        json={
            "title": "Updated Book",
            "author": "Authorized Author",
            "isbn": "978-8888888888",
            "published_year": 2001,
            "member_id": member["id"],
        },
        headers=admin_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["title"] == "Updated Book"
    assert replace_response.json()["published_year"] == 2001

    assert (
        database_client.delete(
            f"/books/{book['id']}", headers=admin_headers
        ).status_code
        == 204
    )
    assert (
        database_client.delete(
            f"/members/{member['id']}", headers=admin_headers
        ).status_code
        == 204
    )