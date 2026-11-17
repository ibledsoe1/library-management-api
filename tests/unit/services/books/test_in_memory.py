"""Unit tests for the in-memory Book service contract."""

import pytest

from app.exceptions import MemberNotFoundError, BookNotFoundError
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
    member = Member(id=1, name="Course API", description="Course demonstration")
    store.members.append(member)
    return member


def book_data(title: str = "Write tests") -> BookInput:
    return BookInput(
        title=title,
        description="Add service tests",
        member_id=1,
    )


def test_create_book_requires_existing_member(
    service: InMemoryBookService,
) -> None:
    with pytest.raises(MemberNotFoundError):
        service.create_book(book_data())


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


def test_replace_book_updates_fields(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    book = service.create_book(book_data("Old"))

    updated = service.replace_book(
        book.id,
        BookInput(
            title="Updated",
            description="Updated description",
            completed=True,
            member_id=1,
        ),
    )

    assert updated.title == "Updated"
    assert updated.description == "Updated description"
    assert updated.completed is True


def test_delete_book_removes_book(
    store: InMemoryStore, service: InMemoryBookService
) -> None:
    add_member(store)
    book = service.create_book(book_data("Delete me"))

    service.delete_book(book.id)

    assert service.list_books() == []