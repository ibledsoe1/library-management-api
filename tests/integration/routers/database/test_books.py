"""Successful-path integration tests for every Book API endpoint."""

from starlette.testclient import TestClient


def test_create_list_and_get_books(database_client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Books."""
    member = create_member(database_client, "Course API")
    first_book = create_book(database_client, member["id"], "First Book")
    second_book = create_book(database_client, member["id"], "Second Book")

    list_response = database_client.get("/books")

    assert list_response.status_code == 200
    assert list_response.json() == [first_book, second_book]

    get_response = database_client.get(f"/books/{first_book['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_book


def test_replace_book_updates_the_public_resource(database_client: TestClient) -> None:
    """PUT replaces Book fields and can assign an existing replacement Member."""
    original_member = create_member(database_client, "Original Member")
    replacement_member = create_member(database_client, "Replacement Member")
    book = create_book(database_client, original_member["id"], "Original Book")

    replace_response = database_client.put(
        f"/books/{book['id']}",
        json={
            "title": "Updated Book",
            "description": "Updated through the API.",
            "completed": True,
            "member_id": replacement_member["id"],
        },
    )

    assert replace_response.status_code == 200
    updated_book = replace_response.json()
    assert updated_book == {
        "id": book["id"],
        "title": "Updated Book",
        "description": "Updated through the API.",
        "completed": True,
        "member_id": replacement_member["id"],
    }

    get_response = database_client.get(f"/books/{book['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_book


def test_delete_book_removes_the_public_resource(database_client: TestClient) -> None:
    """DELETE returns no content and removes a Book from its collection."""
    member = create_member(database_client, "Course API")
    book = create_book(database_client, member["id"], "Deleted Book")

    delete_response = database_client.delete(f"/books/{book['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = database_client.get("/books")
    assert list_response.status_code == 200
    assert list_response.json() == []


# HELPERS


def create_member(database_client: TestClient, name: str) -> dict:
    """Create a parent Member needed by a Book request."""
    response = database_client.post(
        "/members",
        json={
            "name": name,
            "description": f"Description for {name}.",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_book(database_client: TestClient, member_id: int, title: str) -> dict:
    """Create one Book through the public API and return its response body."""
    response = database_client.post(
        "/books",
        json={
            "title": title,
            "description": f"Description for {title}.",
            "completed": False,
            "member_id": member_id,
        },
    )
    assert response.status_code == 201
    return response.json()