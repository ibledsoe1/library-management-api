"""In-memory router integration tests for the Member resource."""

from starlette.testclient import TestClient


def test_member_crud_works_with_memory_client(memory_client: TestClient) -> None:
    """The Member router works when DI selects the in-memory service."""
    create_response = memory_client.post(
        "/members",
        json={
            "name": "Memory Member",
            "description": "Stored by the in-memory service.",
        },
    )

    assert create_response.status_code == 201
    member = create_response.json()

    get_response = memory_client.get(f"/members/{member['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == member

    replace_response = memory_client.put(
        f"/members/{member['id']}",
        json={
            "name": "Updated Memory Member",
            "description": "Updated without PostgreSQL.",
        },
    )
    assert replace_response.status_code == 200

    delete_response = memory_client.delete(f"/members/{member['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert memory_client.get("/members").json() == []


def test_member_books_route_works_with_memory_client(
    memory_client: TestClient,
) -> None:
    """The memory services preserve the Member-to-Book relationship."""
    member = create_member(memory_client)
    book_response = memory_client.post(
        "/books",
        json={
            "title": "Memory Book",
            "description": "Related to an in-memory member.",
            "completed": False,
            "member_id": member["id"],
        },
    )
    assert book_response.status_code == 201

    response = memory_client.get(f"/members/{member['id']}/books")

    assert response.status_code == 200
    assert response.json() == [book_response.json()]


def create_member(memory_client: TestClient) -> dict:
    """Create one Member through the memory-backed public API."""
    response = memory_client.post(
        "/members",
        json={
            "name": "Memory Parent",
            "description": "Parent member for the memory router test.",
        },
    )
    assert response.status_code == 201
    return response.json()