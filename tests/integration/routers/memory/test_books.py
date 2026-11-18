"""In-memory router integration tests for the Book resource."""

from starlette.testclient import TestClient


def test_book_crud_works_with_memory_client(
    memory_client: TestClient, admin_headers: dict[str, str]
) -> None:
    """The Book router works when DI selects the in-memory service."""
    member = create_member(memory_client, admin_headers)
    create_response = memory_client.post(
        "/books",
        json=book_body(member["id"]),
        headers=admin_headers,
    )

    assert create_response.status_code == 201
    book = create_response.json()

    get_response = memory_client.get(f"/books/{book['id']}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json() == book

    replace_response = memory_client.put(
        f"/books/{book['id']}",
        json=book_body(member["id"], title="Updated Memory Book"),
        headers=admin_headers,
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["title"] == "Updated Memory Book"

    delete_response = memory_client.delete(f"/books/{book['id']}", headers=admin_headers)
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/books", headers=admin_headers).json() == []


# HELPERS


def book_body(member_id: int, title: str = "Memory Book") -> dict[str, int | str]:
    """Return a valid Book request body for the memory router tests."""
    return {
        "title": title,
        "author": "Memory Author",
        "isbn": "978-0000000001",
        "published_year": 2020,
        "member_id": member_id,
    }


def create_member(memory_client: TestClient, headers: dict[str, str]) -> dict:
    """Create the parent Member required by a Book request."""
    response = memory_client.post(
        "/members",
        json={
            "name": "Memory Book Parent",
            "email": "memory.parent@collin.edu",
            "membership_id": "M-200",
            "phone": "1234567890",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()