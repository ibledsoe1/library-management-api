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


# ADMINISTRATOR-ONLY WRITES
# A member is authenticated but lacks the administrator role, so write routes
# return 403 before reaching request validation or the service layer.


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/members", {"name": "Member Member", "description": "Denied."}),
        ("PUT", "/members/999999", {"name": "Member Member", "description": "Denied."}),
        ("DELETE", "/members/999999", None),
        (
            "POST",
            "/books",
            {
                "title": "Member Book",
                "description": "Denied.",
                "completed": False,
                "member_id": 999999,
            },
        ),
        (
            "PUT",
            "/books/999999",
            {
                "title": "Member Book",
                "description": "Denied.",
                "completed": False,
                "member_id": 999999,
            },
        ),
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


def test_administrator_can_complete_a_member_and_book_write_workflow(
    database_client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    """An admin token reaches the existing CRUD workflow after authorization."""
    member_response = database_client.post(
        "/members",
        json={"name": "Authorized Member", "description": "Created by an admin."},
        headers=admin_headers,
    )
    assert member_response.status_code == 201
    member = member_response.json()

    book_response = database_client.post(
        "/books",
        json={
            "title": "Authorized Book",
            "description": "Created by an admin.",
            "completed": False,
            "member_id": member["id"],
        },
        headers=admin_headers,
    )
    assert book_response.status_code == 201
    book = book_response.json()

    replace_response = database_client.put(
        f"/books/{book['id']}",
        json={
            "title": "Completed Book",
            "description": "Updated by an admin.",
            "completed": True,
            "member_id": member["id"],
        },
        headers=admin_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["completed"] is True

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