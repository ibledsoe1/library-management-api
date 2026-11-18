"""Unit tests for every Book Pydantic schema and declared rule."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.book import Book
from app.schemas.books import BookInput, BookResponse

CURRENT_YEAR = date.today().year


@pytest.mark.parametrize("missing_field", ["title", "author", "isbn", "member_id"])
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
        ("title", "t" * 201),
        ("author", "   "),
        ("author", "a" * 121),
        ("isbn", "123456789"),  # 9 characters, minimum is 10
        ("published_year", 1449),
        ("published_year", CURRENT_YEAR + 1),
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


@pytest.mark.parametrize("year", [1450, CURRENT_YEAR])
def test_book_create_accepts_published_year_limits(year: int) -> None:
    """The inclusive published-year limits remain valid values."""
    data = valid_book_data()
    data["published_year"] = year

    assert BookInput(**data).published_year == year


def test_book_create_accepts_declared_maximum_lengths() -> None:
    """The inclusive maximum title and author lengths remain valid values."""
    data = valid_book_data()
    data["title"] = "t" * 200
    data["author"] = "a" * 120

    book = BookInput(**data)

    assert len(book.title) == 200
    assert len(book.author) == 120


def test_book_create_defaults_published_year_to_none() -> None:
    """published_year is optional and defaults to None."""
    book = BookInput(**valid_book_data())

    assert book.published_year is None


def test_book_create_strips_whitespace_and_rejects_undocumented_field() -> None:
    """The Book request contract normalizes strings and forbids extra input."""
    data = valid_book_data()
    data["title"] = "  The Hobbit  "
    data["author"] = "  J.R.R. Tolkien  "

    book = BookInput(**data)

    assert book.title == "The Hobbit"
    assert book.author == "J.R.R. Tolkien"

    with pytest.raises(ValidationError):
        BookInput(**valid_book_data(), genre="Fantasy")


def test_book_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Book field rules and configuration."""
    data = valid_book_data()
    data["title"] = "  Updated Title  "
    data["published_year"] = 1999

    book = BookInput(**data)

    assert book.title == "Updated Title"
    assert book.published_year == 1999
    with pytest.raises(ValidationError):
        BookInput(**{**data, "isbn": "short"})


def test_book_response_reads_an_orm_book() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Book(id=1, published_year=1954, **valid_book_data())

    # from_attributes=True lets Pydantic read attributes from a non-dict object.
    # FastAPI does this automatically for response_model, but a direct unit
    # test of the schema must request it.
    response = BookResponse.model_validate(source, from_attributes=True)

    assert response.model_dump() == {
        **valid_book_data(),
        "published_year": 1954,
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
        "title": "The Fellowship Of The Ring",
        "author": "J.R.R. Tolkien",
        "isbn": "978-0547928210",
        "member_id": 1,
    }