"""In-memory router integration tests for the Member resource."""

from starlette.testclient import TestClient


def test_member_crud_works_with_memory_client(
    memory_client: TestClient, admin_headers: dict[str, str]
) -> None:
    """The Member router works when DI selects the in-memory service."""
    create_response = memory_client.post(
        "/members",
        json=member_body(),
        headers=admin_headers,
    )

    assert create_response.status_code == 201
    member = create_response.json()

    get_response = memory_client.get(f"/members/{member['id']}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json() == member

    replace_response = memory_client.put(
        f"/members/{member['id']}",
        json=member_body(name="Updated Memory Member"),
        headers=admin_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["name"] == "Updated Memory Member"

    delete_response = memory_client.delete(
        f"/members/{member['id']}", headers=admin_headers
    )
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/members", headers=admin_headers).json() == []


def test_member_books_route_works_with_memory_client(
    memory_client: TestClient, admin_headers: dict[str, str]
) -> None:
    """The memory services preserve the Member-to-Book relationship."""
    member = create_member(memory_client, admin_headers)
    book_response = memory_client.post(
        "/books",
        json={
            "title": "Memory Book",
            "author": "Memory Author",
            "isbn": "978-0000000001",
            "published_year": 2020,
            "member_id": member["id"],
        },
        headers=admin_headers,
    )
    assert book_response.status_code == 201

    response = memory_client.get(
        f"/members/{member['id']}/books", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json() == [book_response.json()]


# HELPERS


def member_body(name: str = "Memory Member") -> dict[str, str]:
    """Return a valid Member request body for the memory router tests."""
    return {
        "name": name,
        "email": "memory.member@collin.edu",
        "membership_id": "M-100",
        "phone": "1234567890",
    }


def create_member(memory_client: TestClient, headers: dict[str, str]) -> dict:
    """Create one Member through the memory-backed public API."""
    response = memory_client.post("/members", json=member_body(), headers=headers)
    assert response.status_code == 201
    return response.json()