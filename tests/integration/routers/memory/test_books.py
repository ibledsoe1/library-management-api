"""In-memory router integration tests for the Book resource."""

from starlette.testclient import TestClient


def test_book_crud_works_with_memory_client(memory_client: TestClient) -> None:
    """The Book router works when DI selects the in-memory service."""
    member = create_member(memory_client)
    create_response = memory_client.post(
        "/books",
        json={
            "title": "Memory Book",
            "description": "Stored by the in-memory service.",
            "completed": False,
            "member_id": member["id"],
        },
    )

    assert create_response.status_code == 201
    book = create_response.json()

    get_response = memory_client.get(f"/books/{book['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == book

    replace_response = memory_client.put(
        f"/books/{book['id']}",
        json={
            "title": "Updated Memory Book",
            "description": "Updated without PostgreSQL.",
            "completed": True,
            "member_id": member["id"],
        },
    )
    assert replace_response.status_code == 200

    delete_response = memory_client.delete(f"/books/{book['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/books").json() == []


def create_member(memory_client: TestClient) -> dict:
    """Create the parent Member required by a Book request."""
    response = memory_client.post(
        "/members",
        json={
            "name": "Memory Book Parent",
            "description": "Parent member for the memory book test.",
        },
    )
    assert response.status_code == 201
    return response.json()