"""Negative API tests for invalid, missing, and disallowed client requests.

Every write below uses `admin_client`, which sends a valid administrator Bearer
token, so each failure is caused by the request itself and not by security.
"""

import pytest
from starlette.testclient import TestClient


# REQUEST-BODY VALIDATION
# FastAPI passes JSON bodies to Pydantic before the route handler completes.
# These tests verify required fields, unknown fields, and field boundaries.


def test_create_member_rejects_missing_required_field(
    admin_client: TestClient,
) -> None:
    """A request without the required email is rejected with 422."""
    body = member_body("Incomplete Member")
    body.pop("email")

    response = admin_client.post("/members", json=body)

    assert_validation_error(response, field="email", error_type="missing")


def test_create_member_rejects_undocumented_field(
    admin_client: TestClient,
) -> None:
    """extra='forbid' prevents a client from sending an unknown JSON field."""
    response = admin_client.post(
        "/members",
        json={**member_body("Unexpected Field"), "address": "123 Main St"},
    )

    assert_validation_error(response, field="address", error_type="extra_forbidden")


def test_create_book_rejects_missing_required_field(
    admin_client: TestClient,
) -> None:
    """A Book request without the required author is rejected with 422."""
    member = create_member(admin_client, "Izzy Bledsoe")
    body = book_body(member["id"], "Incomplete Book")
    body.pop("author")

    response = admin_client.post("/books", json=body)

    assert_validation_error(response, field="author", error_type="missing")


def test_create_book_rejects_undocumented_field(
    admin_client: TestClient,
) -> None:
    """The Book contract also forbids unknown JSON fields."""
    member = create_member(admin_client, "Izzy Bledsoe")

    response = admin_client.post(
        "/books",
        json={**book_body(member["id"], "Unexpected Field"), "genre": "Fantasy"},
    )

    assert_validation_error(response, field="genre", error_type="extra_forbidden")


# REQUEST-BODY BOUNDARY VALIDATION
# These values have the expected JSON fields but violate Pydantic constraints.


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "   "),  # blank after whitespace stripping
        ("name", "x" * 121),
        ("email", "not-an-email"),
        ("phone", "123-456-7890"),
        ("phone", "123456789"),
    ],
    ids=[
        "blank-name",
        "name-over-maximum",
        "invalid-email",
        "formatted-phone",
        "short-phone",
    ],
)
def test_create_member_rejects_invalid_boundary_values(
    admin_client: TestClient,
    field: str,
    value: str,
) -> None:
    """Pydantic enforces documented Member boundaries over HTTP."""
    response = admin_client.post(
        "/members",
        json={**member_body("Boundary Member"), field: value},
    )

    assert_validation_error(response, field=field)
    assert admin_client.get("/members").json() == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("title", "x" * 201),
        ("author", "x" * 121),
        ("isbn", "123456789"),
        ("published_year", 1449),
        ("published_year", 9999),
    ],
    ids=[
        "blank-title",
        "title-over-maximum",
        "author-over-maximum",
        "short-isbn",
        "year-too-early",
        "year-in-future",
    ],
)
def test_create_book_rejects_invalid_boundary_values(
    admin_client: TestClient,
    field: str,
    value: int | str,
) -> None:
    """Pydantic enforces documented Book boundaries over HTTP."""
    member = create_member(admin_client, "Izzy Bledsoe")

    response = admin_client.post(
        "/books",
        json={**book_body(member["id"], "Boundary Book"), field: value},
    )

    assert_validation_error(response, field=field)
    assert admin_client.get("/books").json() == []


# PATH-PARAMETER VALIDATION
# FastAPI validates the typed `int` path parameters before it calls a route.


@pytest.mark.parametrize(
    "path",
    ["/members/not-an-integer", "/books/not-an-integer"],
    ids=["member-id", "book-id"],
)
def test_typed_path_parameters_reject_wrong_data_type(
    admin_client: TestClient,
    path: str,
) -> None:
    """FastAPI rejects a non-integer resource identifier before the route runs."""
    response = admin_client.get(path)

    assert_validation_error(response)


# MISSING RESOURCES
# Valid requests that point at an identifier with no stored resource return 404.


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/members/999999"),
        ("GET", "/members/999999/books"),
        ("PUT", "/members/999999"),
        ("DELETE", "/members/999999"),
        ("GET", "/books/999999"),
        ("PUT", "/books/999999"),
        ("DELETE", "/books/999999"),
    ],
)
def test_missing_resources_return_not_found(
    admin_client: TestClient, method: str, path: str
) -> None:
    """A valid identifier with no matching resource returns the documented 404."""
    body = None
    if path.startswith("/members") and method == "PUT":
        body = member_body("Missing Member")
    elif path.startswith("/books") and method == "PUT":
        # The parent exists, so the Book itself must be the missing resource.
        member = create_member(admin_client, "Izzy Bledsoe")
        body = book_body(member["id"], "Missing Book")

    response = admin_client.request(method, path, json=body)

    assert response.status_code == 404
    assert response.json()["detail"]


# BUSINESS-RULE REJECTIONS
# These requests have a valid shape, so the application layers decide whether
# the requested relationship or value is allowed and return 404 or 409. Each
# test then confirms the rejected write left stored data unchanged.


def test_create_book_rejects_nonexistent_parent_member(
    admin_client: TestClient,
) -> None:
    """The Book relationship rule becomes a client-visible 404 response."""
    response = admin_client.post("/books", json=book_body(999999, "Orphan Book"))

    assert response.status_code == 404
    assert response.json()["detail"]
    assert admin_client.get("/books").json() == []


def test_replace_book_rejects_nonexistent_parent_member(
    admin_client: TestClient,
) -> None:
    """Moving a Book to a missing Member returns 404 and keeps the old owner."""
    member = create_member(admin_client, "Izzy Bledsoe")
    book = create_book(admin_client, member["id"], "Original Book")

    response = admin_client.put(
        f"/books/{book['id']}", json=book_body(999999, "Original Book")
    )

    assert response.status_code == 404
    assert admin_client.get(f"/books/{book['id']}").json() == book


def test_create_member_rejects_duplicate_email(admin_client: TestClient) -> None:
    """A second Member cannot reuse an existing email."""
    first = create_member(admin_client, "First Member")

    response = admin_client.post(
        "/members",
        json={**member_body("Second Member"), "email": first["email"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]
    assert admin_client.get("/members").json() == [first]


def test_create_member_rejects_duplicate_membership_id(
    admin_client: TestClient,
) -> None:
    """A second Member cannot reuse an existing membership ID."""
    first = create_member(admin_client, "First Member")

    response = admin_client.post(
        "/members",
        json={**member_body("Second Member"), "membership_id": first["membership_id"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]
    assert admin_client.get("/members").json() == [first]


def test_replace_member_rejects_duplicate_email_of_another_member(
    admin_client: TestClient,
) -> None:
    """Replacing a Member with another Member's email returns 409."""
    first = create_member(admin_client, "First Member")
    second = create_member(admin_client, "Second Member")

    response = admin_client.put(
        f"/members/{second['id']}",
        json={**member_body("Second Member"), "email": first["email"]},
    )

    assert response.status_code == 409
    assert admin_client.get(f"/members/{second['id']}").json() == second


def test_create_book_rejects_duplicate_isbn(admin_client: TestClient) -> None:
    """A second Book cannot reuse an existing ISBN."""
    member = create_member(admin_client, "Izzy Bledsoe")
    first = create_book(admin_client, member["id"], "First Book")

    response = admin_client.post(
        "/books",
        json={**book_body(member["id"], "Second Book"), "isbn": first["isbn"]},
    )

    assert response.status_code == 409
    assert response.json()["detail"]
    assert admin_client.get("/books").json() == [first]


def test_replace_book_rejects_duplicate_isbn_of_another_book(
    admin_client: TestClient,
) -> None:
    """Replacing a Book with another Book's ISBN returns 409."""
    member = create_member(admin_client, "Izzy Bledsoe")
    first = create_book(admin_client, member["id"], "First Book")
    second = create_book(admin_client, member["id"], "Second Book")

    response = admin_client.put(
        f"/books/{second['id']}",
        json={**book_body(member["id"], "Second Book"), "isbn": first["isbn"]},
    )

    assert response.status_code == 409
    assert admin_client.get(f"/books/{second['id']}").json() == second


def test_delete_member_rejects_member_with_related_books(
    admin_client: TestClient,
) -> None:
    """A Member with Books remains protected by the documented 409 conflict."""
    member = create_member(admin_client, "Protected Member")
    book = create_book(admin_client, member["id"], "Protected Book")

    response = admin_client.delete(f"/members/{member['id']}")

    assert response.status_code == 409
    assert response.json()["detail"]
    assert admin_client.get(f"/members/{member['id']}").json() == member
    assert admin_client.get(f"/books/{book['id']}").json() == book


# HELPERS


def assert_validation_error(
    response, field: str | None = None, error_type: str | None = None
) -> None:
    """Check FastAPI's stable 422 status and validation-error response shape.

    When `field` is given, also confirm that the error points at that field, so
    a request is not rejected for an unrelated reason.
    """
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail
    if field is not None:
        errors = [error for error in detail if error["loc"][-1] == field]
        assert errors, f"no validation error located at {field!r}: {detail}"
        if error_type is not None:
            assert errors[0]["type"] == error_type


def member_body(name: str) -> dict[str, str]:
    """Return a valid Member request body whose unique fields come from the name."""
    return {
        "name": name,
        "email": f"{name.lower().replace(' ', '.')}@collin.edu",
        "membership_id": name.upper().replace(" ", "-"),
        "phone": "1234567890",
    }


def book_body(member_id: int, title: str) -> dict[str, int | str]:
    """Return a valid Book request body whose ISBN comes from the title."""
    return {
        "title": title,
        "author": "Test Author",
        "isbn": f"ISBN-{title.upper().replace(' ', '-')}",
        "published_year": 2000,
        "member_id": member_id,
    }


def create_member(client: TestClient, name: str) -> dict:
    """Create a Member through the public API and return its response body."""
    response = client.post("/members", json=member_body(name))
    assert response.status_code == 201
    return response.json()


def create_book(client: TestClient, member_id: int, title: str) -> dict:
    """Create a Book through the public API and return its response body."""
    response = client.post("/books", json=book_body(member_id, title))
    assert response.status_code == 201
    return response.json()