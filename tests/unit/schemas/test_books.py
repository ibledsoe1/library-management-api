"""Unit tests for every Book Pydantic schema and declared rule."""

import pytest
from pydantic import ValidationError

from app.models.book import Book
from app.schemas.books import BookInput, BookResponse


@pytest.mark.parametrize("missing_field", ["title", "description", "member_id"])
def test_book_create_requires_each_declared_required_field(missing_field: str) -> None:
    """A create request must include every required Book field."""
    data = valid_book_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        BookInput(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", "   "),
        ("description", "   "),
        ("title", "t" * 121),
        ("description", "d" * 501),
        ("member_id", 0),
        ("member_id", -1),
    ],
)
def test_book_create_enforces_field_boundaries(
    field_name: str,
    value: int | str,
) -> None:
    """Book fields must satisfy their declared constraints."""
    data = valid_book_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        BookInput(**data)


def test_book_create_accepts_declared_maximum_lengths_and_positive_id() -> None:
    """The inclusive limits and a positive Member ID remain valid values."""
    book = BookInput(
        title="t" * 120,
        description="d" * 500,
        member_id=1,
    )

    assert len(book.title) == 120
    assert len(book.description) == 500
    assert book.member_id == 1


def test_book_create_defaults_completed_to_false() -> None:
    """A new Book is incomplete unless the client explicitly marks it complete."""
    book = BookInput(**valid_book_data())

    assert book.completed is False


def test_book_create_strips_whitespace_and_rejects_undocumented_field() -> None:
    """The Book request contract normalizes strings and forbids extra input."""
    book = BookInput(
        title="  Write tests  ",
        description="  Add schema unit tests.  ",
        member_id=1,
    )

    assert book.title == "Write tests"
    assert book.description == "Add schema unit tests."

    with pytest.raises(ValidationError):
        BookInput(**valid_book_data(), priority="high")


def test_book_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Book field rules and configuration."""
    book = BookInput(
        title="  Update tests  ",
        description="  Replace every editable field.  ",
        completed=True,
        member_id=1,
    )

    assert book.title == "Update tests"
    assert book.description == "Replace every editable field."
    assert book.completed is True


def test_book_response_reads_an_orm_book() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Book(
        id=1,
        title="Write tests",
        description="Add schema unit tests.",
        completed=False,
        member_id=1,
    )

    response = BookResponse.model_validate(source)

    assert response.model_dump() == {
        "title": "Write tests",
        "description": "Add schema unit tests.",
        "completed": False,
        "member_id": 1,
        "id": 1,
    }


def test_book_response_rejects_nonpositive_server_id() -> None:
    """A response must contain a positive server-generated identifier."""
    with pytest.raises(ValidationError):
        BookResponse(**valid_book_data(), id=0)


# HELPERS


def valid_book_data() -> dict[str, int | str]:
    """Return a valid Book request body for focused validation scenarios."""
    return {
        "title": "Write tests",
        "description": "Add schema unit tests.",
        "member_id": 1,
    }