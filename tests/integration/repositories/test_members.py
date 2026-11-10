"""PostgreSQL integration tests for every MemberRepository method."""

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
        MemberInput(name="Created Member", description="Created by repository.")
    )
    db_session.commit()

    assert created.id > 0
    stored = repository.get_by_id(created.id)
    assert stored is not None
    assert stored.name == "Created Member"
    assert stored.description == "Created by repository."


def test_replace_updates_persisted_member(db_session: Session) -> None:
    """replace changes both editable Member columns in PostgreSQL."""
    repository = MemberRepository(db_session)
    member = create_member(repository, db_session, "Original Member")

    updated = repository.replace(
        member,
        MemberInput(name="Updated Member", description="Updated description."),
    )
    db_session.commit()
    db_session.refresh(updated)

    assert updated.name == "Updated Member"
    assert updated.description == "Updated description."


def test_delete_removes_persisted_member(db_session: Session) -> None:
    """delete removes a Member row after its transaction is committed."""
    repository = MemberRepository(db_session)
    member = create_member(repository, db_session, "Deleted Member")

    repository.delete(member)
    db_session.commit()

    assert repository.get_by_id(member.id) is None


# HELPERS


def create_member(repository: MemberRepository, session: Session, name: str):
    """Create and commit one Member used by a repository test."""
    member = repository.create(
        MemberInput(name=name, description=f"Description for {name}.")
    )
    session.commit()
    session.refresh(member)
    return member