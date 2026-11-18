"""Successful-path integration tests for every Member API endpoint."""

from starlette.testclient import TestClient

# `admin_client` is a database-backed TestClient that already sends the
# administrator Bearer token, so these tests focus on Member behavior.


def test_create_list_and_get_members(admin_client: TestClient) -> None:
    """POST, GET collection, and GET item work together for Members."""
    first_member = create_member(admin_client, "First Member")
    second_member = create_member(admin_client, "Second Member")

    list_response = admin_client.get("/members")

    assert list_response.status_code == 200
    assert list_response.json() == [first_member, second_member]

    get_response = admin_client.get(f"/members/{first_member['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == first_member


def test_replace_member_updates_the_public_resource(admin_client: TestClient) -> None:
    """PUT replaces a Member and later GET returns the new values."""
    member = create_member(admin_client, "Original Member")

    replace_response = admin_client.put(
        f"/members/{member['id']}",
        json={
            "name": "Updated Member",
            "email": "updated.member@collin.edu",
            "membership_id": "UPDATED-1",
            "phone": "5559876543",
        },
    )

    assert replace_response.status_code == 200
    updated_member = replace_response.json()
    assert updated_member == {
        "id": member["id"],
        "name": "Updated Member",
        "email": "updated.member@collin.edu",
        "membership_id": "UPDATED-1",
        "phone": "5559876543",
    }

    get_response = admin_client.get(f"/members/{member['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == updated_member


def test_delete_member_removes_the_public_resource(admin_client: TestClient) -> None:
    """DELETE returns no content and removes a Member from its collection."""
    member = create_member(admin_client, "Deleted Member")

    delete_response = admin_client.delete(f"/members/{member['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    list_response = admin_client.get("/members")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_list_member_books_returns_related_books(admin_client: TestClient) -> None:
    """The related-resource endpoint returns Books for the requested Member."""
    member = create_member(admin_client, "Izzy Bledsoe")
    other_member = create_member(admin_client, "Other Member")

    first_book_response = admin_client.post(
        "/books", json=book_body(member["id"], "First Book")
    )
    second_book_response = admin_client.post(
        "/books", json=book_body(member["id"], "Second Book")
    )
    # A Book owned by someone else must not appear in the first Member's list.
    admin_client.post("/books", json=book_body(other_member["id"], "Other Book"))
    assert first_book_response.status_code == 201
    assert second_book_response.status_code == 201

    response = admin_client.get(f"/members/{member['id']}/books")

    assert response.status_code == 200
    assert response.json() == [first_book_response.json(), second_book_response.json()]


# HELPERS


def create_member(client: TestClient, name: str) -> dict:
    """Create one Member through the public API and return its response body."""
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


def book_body(member_id: int, title: str) -> dict:
    """Return a valid Book request body for a related-Book scenario."""
    return {
        "title": title,
        "author": "Test Author",
        "isbn": f"ISBN-{title.upper().replace(' ', '-')}",
        "published_year": 2000,
        "member_id": member_id,
    }