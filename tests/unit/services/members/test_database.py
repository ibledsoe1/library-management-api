"""Unit tests for DatabaseMemberService with mocked repositories."""

from collections.abc import Generator

import pytest
from mockito import args, mock, unstub, verify, when

import app.services.members.database as database_module
from app.exceptions import MemberNotFoundError
from app.models.member import Member
from app.schemas.members import MemberInput
from app.services.members import DatabaseMemberService


# this fixture is local to this file instead of in conftest.pt because only these
# service tests need fake sessions
@pytest.fixture
def session_factory() -> Generator[tuple[object, object, object], None, None]:
    """Build fake database collaborators for service unit tests.

    The service uses two session-factory forms:

    * ``session_factory()`` opens a Session for reads.
    * ``session_factory.begin()`` opens a transaction for writes.

    The context-manager stubs are needed because the production service uses
    ``with``. Python enters a context manager by calling ``__enter__`` and
    leaves it by calling ``__exit__``; Mockito must provide those methods so
    the fake factory can yield the fake Session. The third returned mock is the
    repository that the test injects into the service.
    """
    session = mock()
    factory = mock()
    repository = mock()
    read_context = mock()
    transaction_context = mock()

    # Simulate: ``with session_factory() as session``.
    when(read_context).__enter__().thenReturn(session)
    # `__exit__` receives exception type, value, and traceback; Mockito's
    # `args` matcher accepts any values for those cleanup arguments.
    when(read_context).__exit__(*args)
    when(factory).__call__().thenReturn(read_context)

    # Simulate: ``with session_factory.begin() as session``.
    when(transaction_context).__enter__().thenReturn(session)
    # Match all arguments passed when Python leaves the `with` block.
    when(transaction_context).__exit__(*args)
    when(factory).begin().thenReturn(transaction_context)

    try:
        # Yield the fake collaborators to the test. Pytest pauses this fixture
        # here while the test runs.
        yield factory, session, repository
    finally:
        # Remove Mockito stubs so they cannot affect a later test.
        unstub()
        
# This is testing the service's own job, coordinating
# We check that repository, session, and factory are called once, not what they do
def test_create_member_uses_repository_and_transaction(
    session_factory: tuple[object, object, object],
) -> None:
    factory, session, repository = session_factory
    member = Member(id=1, name="Course API", description="Demo")
    when(repository).create(...).thenReturn(member)

    with when(database_module).MemberRepository(session).thenReturn(repository):
        result = DatabaseMemberService(factory).create_member(
            MemberInput(name="Member Fields", description="Demo")
        )

    assert result is member
    verify(repository, times=1).create(...)
    verify(session, times=1).refresh(member)
    verify(factory, times=1).begin()


def test_get_member_translates_missing_repository_result(
    session_factory: tuple[object, object, object],
) -> None:
    factory, session, repository = session_factory
    when(repository).get_by_id(999).thenReturn(None)

    with when(database_module).MemberRepository(session).thenReturn(repository):
        with pytest.raises(MemberNotFoundError):
            DatabaseMemberService(factory).get_member(999)