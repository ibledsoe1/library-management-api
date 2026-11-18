"""PostgreSQL integration tests for every MemberRepository method."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.members import MemberRepository
from app.schemas.members import MemberInput


def test_list_all_returns_members_in_id_order(db_session: Session) -> None:
    """list_all persists and returns Members in the repository's declared order."""
    repository = MemberRepository(db_session)
    first = create_member(repository, db_session, "First Member")
    second = create_member(repository, db_session, "Second Member")

    members = repository.list_all()

    assert [member.id for member in members] == [first.id, second.id]


def test_get_by_id_returns_existing_member_and_none_when_missing(
    db_session: Session,
) -> None:
    """get_by_id distinguishes a persisted Member from an absent ID."""
    repository = MemberRepository(db_session)
    created = create_member(repository, db_session, "Stored Member")

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Stored Member"
    assert repository.get_by_id(999) is None


def test_create_persists_member_and_generates_id(db_session: Session) -> None:
    """create maps request data to a PostgreSQL row with a generated ID."""
    repository = MemberRepository(db_session)

    created = repository.create(
        member_input("Created Member", phone="5551234567")
    )
    db_session.commit()

    assert created.id > 0
    stored = repository.get_by_id(created.id)
    assert stored is not None
    assert stored.name == "Created Member"
    assert stored.email == "created.member@collin.edu"
    assert stored.membership_id == "CREATED-MEMBER"
    assert stored.phone == "5551234567"


def test_replace_updates_persisted_member(db_session: Session) -> None:
    """replace changes every editable Member column in PostgreSQL."""
    repository = MemberRepository(db_session)
    member = create_member(repository, db_session, "Original Member")

    updated = repository.replace(
        member,
        member_input("Updated Member", phone="5559876543"),
    )
    db_session.commit()
    db_session.refresh(updated)

    assert updated.name == "Updated Member"
    assert updated.email == "updated.member@collin.edu"
    assert updated.membership_id == "UPDATED-MEMBER"
    assert updated.phone == "5559876543"


def test_delete_removes_persisted_member(db_session: Session) -> None:
    """delete removes a Member row after its transaction is committed."""
    repository = MemberRepository(db_session)
    member = create_member(repository, db_session, "Deleted Member")

    repository.delete(member)
    db_session.commit()

    assert repository.get_by_id(member.id) is None


# UNIQUE CONSTRAINTS
# Only a real PostgreSQL database can prove these rules. The service layer reads
# the constraint name from the IntegrityError to decide which 409 to raise, so
# the names are part of the contract being tested.


def test_create_enforces_unique_email(db_session: Session) -> None:
    """A second Member with the same email violates uq_members_email."""
    repository = MemberRepository(db_session)
    create_member(repository, db_session, "First Member")

    with pytest.raises(IntegrityError) as error:
        repository.create(
            member_input(
                "Second Member", email=email_for("First Member")
            )
        )
    db_session.rollback()

    assert error.value.orig.diag.constraint_name == "uq_members_email"
    assert len(repository.list_all()) == 1


def test_create_enforces_unique_membership_id(db_session: Session) -> None:
    """A second Member with the same membership ID violates uq_membership_id."""
    repository = MemberRepository(db_session)
    create_member(repository, db_session, "First Member")

    with pytest.raises(IntegrityError) as error:
        repository.create(
            member_input(
                "Second Member", membership_id=membership_id_for("First Member")
            )
        )
    db_session.rollback()

    assert error.value.orig.diag.constraint_name == "uq_membership_id"
    assert len(repository.list_all()) == 1


# HELPERS


def email_for(name: str) -> str:
    return f"{name.lower().replace(' ', '.')}@collin.edu"


def membership_id_for(name: str) -> str:
    return name.upper().replace(" ", "-")


def member_input(
    name: str,
    email: str | None = None,
    membership_id: str | None = None,
    phone: str = "1234567890",
) -> MemberInput:
    """Build a valid MemberInput whose unique fields are derived from the name."""
    return MemberInput(
        name=name,
        email=email or email_for(name),
        membership_id=membership_id or membership_id_for(name),
        phone=phone,
    )


def create_member(repository: MemberRepository, session: Session, name: str):
    """Create and commit one Member used by a repository test."""
    member = repository.create(member_input(name))
    session.commit()
    session.refresh(member)
    return member