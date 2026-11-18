"""Unit tests for the in-memory Book service contract."""

import pytest

from app.exceptions import (
    BookNotFoundError,
    ISBNAlreadyExistsError,
    MemberNotFoundError,
)
from app.models.member import Member
from app.schemas.books import BookInput
from app.services.in_memory_store import InMemoryStore
from app.services.books import InMemoryBookService


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def service(store: InMemoryStore) -> InMemoryBookService:
    return InMemoryBookService(store)


def add_member(store: InMemoryStore) -> Member:
    member = Member(
        id=1,
        name="Izzy Bledsoe",
        email="ibledsoe1@collin.edu",
        membership_id="101",
        phone="1234567890",
    )
    store.members.append(member)
    return member


def book_data(
    title: str = "The Hobbit",
    isbn: str = "978-0547928225",
    member_id: int = 1,
) -> BookInput:
    return BookInput(
        title=title,
        author="J.R.R. Tolkien",
        isbn=isbn,
        published_year=1937,
        member_id=member_id,
    )


def test_create_book_requires_existing_member(
    service: InMemoryBookService,
) -> None:
    with pytest.raises(MemberNotFoundError):
        service.create_book(book_data())

    assert service.list_books() == []


def test_create_list_and_get_book(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)

    created = service.create_book(book_data())

    assert created.id == 1
    assert service.list_books() == [created]
    assert service.get_book(created.id) is created


def test_get_book_raises_for_missing_id(service: InMemoryBookService) -> None:
    with pytest.raises(BookNotFoundError):
        service.get_book(999)


def test_create_book_rejects_duplicate_isbn(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    service.create_book(book_data())

    with pytest.raises(ISBNAlreadyExistsError):
        service.create_book(book_data(title="Another Title"))

    assert len(service.list_books()) == 1


def test_replace_book_updates_fields(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    book = service.create_book(book_data("Old"))

    updated = service.replace_book(
        book.id,
        book_data(title="Updated", isbn="978-0547928226"),
    )

    assert updated.title == "Updated"
    assert updated.isbn == "978-0547928226"


def test_replace_book_requires_existing_member(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    book = service.create_book(book_data("Original"))

    with pytest.raises(MemberNotFoundError):
        service.replace_book(book.id, book_data(title="Changed", member_id=999))

    assert book.title == "Original"


def test_delete_book_removes_book(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    book = service.create_book(book_data("Delete me"))

    service.delete_book(book.id)

    assert service.list_books() == []