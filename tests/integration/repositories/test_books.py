"""PostgreSQL integration tests for every BookRepository method and ORM relation."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.members import MemberRepository
from app.repositories.books import BookRepository
from app.schemas.members import MemberInput
from app.schemas.books import BookInput


def test_list_all_returns_books_in_id_order(db_session: Session) -> None:
    """list_all persists and returns Books in the repository's declared order."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)
    first = create_book(repository, db_session, member.id, "First Book")
    second = create_book(repository, db_session, member.id, "Second Book")

    books = repository.list_all()

    assert [book.id for book in books] == [first.id, second.id]


def test_list_by_member_filters_related_books(db_session: Session) -> None:
    """list_by_member returns only Books belonging to the requested Member."""
    first_member = create_member(db_session, "First Member")
    second_member = create_member(db_session, "Second Member")
    repository = BookRepository(db_session)
    first_book = create_book(repository, db_session, first_member.id, "First Book")
    create_book(repository, db_session, second_member.id, "Second Book")

    books = repository.list_by_member(first_member.id)

    assert [book.id for book in books] == [first_book.id]
    assert all(book.member_id == first_member.id for book in books)


def test_get_by_id_returns_existing_book_and_none_when_missing(
    db_session: Session,
) -> None:
    """get_by_id distinguishes a persisted Book from an absent ID."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)
    created = create_book(repository, db_session, member.id, "Stored Book")

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.title == "Stored Book"
    assert repository.get_by_id(999) is None


def test_exists_for_member_reports_related_book_presence(db_session: Session) -> None:
    """exists_for_member changes from false to true after Book creation."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)

    assert repository.exists_for_member(member.id) is False

    create_book(repository, db_session, member.id, "Stored Book")

    assert repository.exists_for_member(member.id) is True


def test_create_persists_book_and_generates_id(db_session: Session) -> None:
    """create maps Book request data to a PostgreSQL row with a generated ID."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)

    created = repository.create(
        BookInput(
            title="Created Book",
            author="Created Author",
            isbn="978-1111111111",
            published_year=2001,
            member_id=member.id,
        )
    )
    db_session.commit()

    assert created.id > 0
    stored = repository.get_by_id(created.id)
    assert stored is not None
    assert stored.title == "Created Book"
    assert stored.author == "Created Author"
    assert stored.isbn == "978-1111111111"
    assert stored.published_year == 2001
    assert stored.member_id == member.id


def test_create_allows_missing_published_year(db_session: Session) -> None:
    """published_year is optional and is stored as NULL when omitted."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)

    created = repository.create(
        BookInput(
            title="Undated Book",
            author="Unknown Author",
            isbn="978-2222222222",
            member_id=member.id,
        )
    )
    db_session.commit()

    assert repository.get_by_id(created.id).published_year is None


def test_replace_updates_all_editable_book_columns(db_session: Session) -> None:
    """replace updates Book fields, including its Member relationship ID."""
    original_member = create_member(db_session, "Original Member")
    replacement_member = create_member(db_session, "Replacement Member")
    repository = BookRepository(db_session)
    book = create_book(repository, db_session, original_member.id, "Original Book")

    updated = repository.replace(
        book,
        BookInput(
            title="Updated Book",
            author="Updated Author",
            isbn="978-3333333333",
            published_year=1999,
            member_id=replacement_member.id,
        ),
    )
    db_session.commit()
    db_session.refresh(updated)

    assert updated.title == "Updated Book"
    assert updated.author == "Updated Author"
    assert updated.isbn == "978-3333333333"
    assert updated.published_year == 1999
    assert updated.member_id == replacement_member.id


def test_delete_removes_persisted_book(db_session: Session) -> None:
    """delete removes a Book row after its transaction is committed."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)
    book = create_book(repository, db_session, member.id, "Deleted Book")

    repository.delete(book)
    db_session.commit()

    assert repository.get_by_id(book.id) is None


# CONSTRAINTS AND RELATIONSHIPS
# Only a real PostgreSQL database enforces these rules.


def test_create_enforces_unique_isbn(db_session: Session) -> None:
    """A second Book with the same ISBN violates uq_books_isbn."""
    member = create_member(db_session, "Izzy Bledsoe")
    repository = BookRepository(db_session)
    create_book(repository, db_session, member.id, "First Book")

    with pytest.raises(IntegrityError) as error:
        repository.create(
            BookInput(
                title="Duplicate Isbn Book",
                author="Test Author",
                isbn=isbn_for("First Book"),
                member_id=member.id,
            )
        )
    db_session.rollback()

    assert error.value.orig.diag.constraint_name == "uq_books_isbn"
    assert len(repository.list_all()) == 1


def test_create_enforces_book_member_foreign_key(db_session: Session) -> None:
    """The Book ORM mapping cannot persist a nonexistent Member reference."""
    repository = BookRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            BookInput(
                title="Orphan Book",
                author="Unknown Author",
                isbn="978-4444444444",
                member_id=999,
            )
        )

    db_session.rollback()


def test_member_with_books_cannot_be_deleted_by_the_database(
    db_session: Session,
) -> None:
    """The database blocks deleting a Member that still has Books."""
    member = create_member(db_session, "Izzy Bledsoe")
    book_repository = BookRepository(db_session)
    create_book(book_repository, db_session, member.id, "Related Book")

    with pytest.raises(IntegrityError):
        MemberRepository(db_session).delete(member)
        db_session.commit()
    db_session.rollback()

    assert MemberRepository(db_session).get_by_id(member.id) is not None
    assert book_repository.exists_for_member(member.id) is True


# HELPERS


def isbn_for(title: str) -> str:
    return f"ISBN-{title.upper().replace(' ', '-')}"


def create_member(session: Session, name: str):
    """Create a persisted parent Member for Book repository scenarios."""
    repository = MemberRepository(session)
    member = repository.create(
        MemberInput(
            name=name,
            email=f"{name.lower().replace(' ', '.')}@collin.edu",
            membership_id=name.upper().replace(" ", "-"),
            phone="1234567890",
        )
    )
    session.commit()
    session.refresh(member)
    return member


def create_book(
    repository: BookRepository,
    session: Session,
    member_id: int,
    title: str,
):
    """Create and commit one Book used by a repository test."""
    book = repository.create(
        BookInput(
            title=title,
            author="Test Author",
            isbn=isbn_for(title),
            published_year=2000,
            member_id=member_id,
        )
    )
    session.commit()
    session.refresh(book)
    return book