"""Successful-path integration tests for every Member API endpoint."""

from starlette.testclient import TestClient


def test_create_list_and_get_members(database_client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Members."""
    first_member = create_member(database_client, "First Member")
    second_member = create_member(database_client, "Second Member")

    list_response = database_client.get("/members")

    assert list_response.status_code == 200
    assert list_response.json() == [first_member, second_member]

    get_response = database_client.get(f"/members/{first_member['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_member


def test_replace_member_updates_the_public_resource(database_client: TestClient) -> None:
    """PUT replaces a Member and later GET returns the new values."""
    member = create_member(database_client, "Original Member")

    replace_response = database_client.put(
        f"/members/{member['id']}",
        json={
            "name": "Updated Member",
            "description": "Updated through the API.",
        },
    )

    assert replace_response.status_code == 200
    updated_member = replace_response.json()
    assert updated_member == {
        "id": member["id"],
        "name": "Updated Member",
        "description": "Updated through the API.",
    }

    get_response = database_client.get(f"/members/{member['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_member


def test_delete_member_removes_the_public_resource(database_client: TestClient) -> None:
    """DELETE returns no content and removes a Member from its collection."""
    member = create_member(database_client, "Deleted Member")

    delete_response = database_client.delete(f"/members/{member['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = database_client.get("/members")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_list_member_books_returns_related_books(database_client: TestClient) -> None:
    """The related-resource endpoint returns Books for the requested Member."""
    member = create_member(database_client, "Course API")

    first_book_response = database_client.post(
        "/books",
        json={
            "title": "First Book",
            "description": "First related Book.",
            "completed": False,
            "member_id": member["id"],
        },
    )
    second_book_response = database_client.post(
        "/books",
        json={
            "title": "Second Book",
            "description": "Second related Book.",
            "completed": True,
            "member_id": member["id"],
        },
    )
    assert first_book_response.status_code == 201
    assert second_book_response.status_code == 201

    response = database_client.get(f"/members/{member['id']}/books")

    assert response.status_code == 200
    assert response.json() == [first_book_response.json(), second_book_response.json()]


# HELPERS


def create_member(database_client: TestClient, name: str) -> dict:
    """Create one Member through the public API and return its response body."""
    response = database_client.post(
        "/members",
        json={
            "name": name,
            "description": f"Description for {name}.",
        },
    )
    assert response.status_code == 201
    return response.json()