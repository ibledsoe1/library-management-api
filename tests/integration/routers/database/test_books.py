"""Successful-path integration tests for every Book API endpoint."""

from starlette.testclient import TestClient

# `admin_client` is a database-backed TestClient that already sends the
# administrator Bearer token, so these tests focus on Book behavior.


def test_create_list_and_get_books(admin_client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Books."""
    member = create_member(admin_client, "Izzy Bledsoe")
    first_book = create_book(admin_client, member["id"], "First Book")
    second_book = create_book(admin_client, member["id"], "Second Book")

    list_response = admin_client.get("/books")

    assert list_response.status_code == 200
    assert list_response.json() == [first_book, second_book]

    get_response = admin_client.get(f"/books/{first_book['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_book


def test_create_book_without_published_year_returns_null(
    admin_client: TestClient,
) -> None:
    """published_year is optional and is returned as null when omitted."""
    member = create_member(admin_client, "Izzy Bledsoe")

    response = admin_client.post(
        "/books",
        json={
            "title": "Undated Book",
            "author": "Unknown Author",
            "isbn": "978-5555555555",
            "member_id": member["id"],
        },
    )

    assert response.status_code == 201
    assert response.json()["published_year"] is None


def test_replace_book_updates_the_public_resource(admin_client: TestClient) -> None:
    """PUT replaces Book fields and can assign an existing replacement Member."""
    original_member = create_member(admin_client, "Original Member")
    replacement_member = create_member(admin_client, "Replacement Member")
    book = create_book(admin_client, original_member["id"], "Original Book")

    replace_response = admin_client.put(
        f"/books/{book['id']}",
        json={
            "title": "Updated Book",
            "author": "Updated Author",
            "isbn": "978-6666666666",
            "published_year": 1999,
            "member_id": replacement_member["id"],
        },
    )

    assert replace_response.status_code == 200
    updated_book = replace_response.json()
    assert updated_book == {
        "id": book["id"],
        "title": "Updated Book",
        "author": "Updated Author",
        "isbn": "978-6666666666",
        "published_year": 1999,
        "member_id": replacement_member["id"],
    }

    get_response = admin_client.get(f"/books/{book['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_book


def test_delete_book_removes_the_public_resource(admin_client: TestClient) -> None:
    """DELETE returns no content and removes a Book from its collection."""
    member = create_member(admin_client, "Izzy Bledsoe")
    book = create_book(admin_client, member["id"], "Deleted Book")

    delete_response = admin_client.delete(f"/books/{book['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = admin_client.get("/books")
    assert list_response.status_code == 200
    assert list_response.json() == []


# HELPERS


def create_member(client: TestClient, name: str) -> dict:
    """Create a parent Member needed by a Book request."""
    response = client.post(
        "/members",
        json={
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@collin.edu",
            "membership_id": name.upper().replace(" ", "-"),
            "phone": "1234567890",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_book(client: TestClient, member_id: int, title: str) -> dict:
    """Create one Book through the public API and return its response body."""
    response = client.post(
        "/books",
        json={
            "title": title,
            "author": "Test Author",
            "isbn": f"ISBN-{title.upper().replace(' ', '-')}",
            "published_year": 2000,
            "member_id": member_id,
        },
    )
    assert response.status_code == 201
    return response.json()