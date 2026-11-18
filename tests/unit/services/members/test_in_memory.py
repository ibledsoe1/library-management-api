"""Unit tests for the in-memory Member service contract."""

import pytest

from app.exceptions import (
    EmailAlreadyExistsError,
    MemberHasBooksError,
    MemberNotFoundError,
    MembershipIdAlreadyExistsError,
)
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


def member_data(
    name: str = "Izzy Bledsoe",
    email: str = "ibledsoe1@collin.edu",
    membership_id: str = "101",
) -> MemberInput:
    return MemberInput(
        name=name,
        email=email,
        membership_id=membership_id,
        phone="1234567890",
    )


def related_book(member_id: int) -> Book:
    return Book(
        id=1,
        title="The Hobbit",
        author="J.R.R. Tolkien",
        isbn="978-0547928225",
        published_year=1937,
        member_id=member_id,
    )


def test_create_list_and_get_member(service: InMemoryMemberService) -> None:
    created = service.create_member(member_data())

    assert created.id == 1
    assert service.list_members() == [created]
    assert service.get_member(created.id) is created


def test_get_member_raises_for_missing_id(service: InMemoryMemberService) -> None:
    with pytest.raises(MemberNotFoundError):
        service.get_member(999)


def test_create_member_rejects_duplicate_email(
    service: InMemoryMemberService,
) -> None:
    service.create_member(member_data())

    with pytest.raises(EmailAlreadyExistsError):
        service.create_member(member_data(membership_id="102"))

    assert len(service.list_members()) == 1


def test_create_member_rejects_duplicate_membership_id(
    service: InMemoryMemberService,
) -> None:
    service.create_member(member_data())

    with pytest.raises(MembershipIdAlreadyExistsError):
        service.create_member(member_data(email="other@collin.edu"))

    assert len(service.list_members()) == 1


def test_replace_member_updates_fields(service: InMemoryMemberService) -> None:
    member = service.create_member(member_data())

    updated = service.replace_member(
        member.id,
        member_data(
            name="Updated Member",
            email="updated@collin.edu",
            membership_id="202",
        ),
    )

    assert updated is member
    assert updated.name == "Updated Member"
    assert updated.email == "updated@collin.edu"
    assert updated.membership_id == "202"


def test_replace_member_rejects_duplicate_email_of_another_member(
    service: InMemoryMemberService,
) -> None:
    service.create_member(member_data())
    second = service.create_member(
        member_data(email="second@collin.edu", membership_id="102")
    )

    with pytest.raises(EmailAlreadyExistsError):
        service.replace_member(
            second.id, member_data(email="ibledsoe1@collin.edu", membership_id="102")
        )

    assert second.email == "second@collin.edu"


def test_list_member_books_requires_existing_member(
    service: InMemoryMemberService,
) -> None:
    with pytest.raises(MemberNotFoundError):
        service.list_member_books(999)


def test_list_member_books_returns_related_books(
    store: InMemoryStore, service: InMemoryMemberService
) -> None:
    member = service.create_member(member_data())
    book = related_book(member.id)
    store.books.append(book)

    assert service.list_member_books(member.id) == [book]


def test_delete_member_rejects_related_books(
    store: InMemoryStore, service: InMemoryMemberService
) -> None:
    member = service.create_member(member_data())
    store.books.append(related_book(member.id))

    with pytest.raises(MemberHasBooksError):
        service.delete_member(member.id)

    assert service.get_member(member.id) is member


def test_delete_member_removes_member_without_books(
    service: InMemoryMemberService,
) -> None:
    member = service.create_member(member_data())

    service.delete_member(member.id)

    assert service.list_members() == []