"""Unit tests for the in-memory Member service contract."""

import pytest

from app.exceptions import MemberHasBooksError, MemberNotFoundError
from app.models.book import Book
from app.schemas.members import MemberInput
from app.services.in_memory_store import InMemoryStore
from app.services.members import InMemoryMemberService


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def service(store: InMemoryStore) -> InMemoryMemberService:
    return InMemoryMemberService(store)


def member_data(name: str = "Course API") -> MemberInput:
    return MemberInput(name=name, description="Course demonstration")


def test_create_list_and_get_member(service: InMemoryMemberService) -> None:
    created = service.create_member(member_data())

    assert created.id == 1
    assert service.list_members() == [created]
    assert service.get_member(created.id) is created


def test_get_member_raises_for_missing_id(service: InMemoryMemberService) -> None:
    with pytest.raises(MemberNotFoundError):
        service.get_member(999)


def test_replace_member_updates_fields(service: InMemoryMemberService) -> None:
    member = service.create_member(member_data())

    updated = service.replace_member(
        member.id,
        MemberInput(name="Updated API", description="Updated description"),
    )

    assert updated is member
    assert updated.name == "Updated API"
    assert updated.description == "Updated description"


def test_list_member_books_requires_existing_member(
    service: InMemoryMemberService,
) -> None:
    with pytest.raises(MemberNotFoundError):
        service.list_member_books(999)


def test_list_member_books_returns_related_books(
    store: InMemoryStore, service: InMemoryMemberService
) -> None:
    member = service.create_member(member_data())
    book = Book(
        id=1,
        title="Book",
        description="Related book",
        completed=False,
        member_id=member.id,
    )
    store.books.append(book)

    assert service.list_member_books(member.id) == [book]


def test_delete_member_rejects_related_books(
    store: InMemoryStore, service: InMemoryMemberService
) -> None:
    member = service.create_member(member_data())
    store.books.append(
        Book(
            id=1,
            title="Book",
            description="Related book",
            completed=False,
            member_id=member.id,
        )
    )

    with pytest.raises(MemberHasBooksError):
        service.delete_member(member.id)

    assert service.get_member(member.id) is member


def test_delete_member_removes_member_without_books(
    service: InMemoryMemberService,
) -> None:
    member = service.create_member(member_data())

    service.delete_member(member.id)

    assert service.list_members() == []