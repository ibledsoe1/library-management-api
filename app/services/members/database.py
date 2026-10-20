"""Relational-database Member service implementation."""

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    MemberHasBooksError, 
    MemberNotFoundError,
    EmailAlreadyExistsError,
    MembershipIdAlreadyExistsError
)
from app.models.member import Member
from app.models.book import Book
from app.repositories.members import MemberRepository
from app.repositories.books import BookRepository
from app.schemas.members import MemberInput
from .base import MemberService

class DatabaseMemberService(MemberService):
    """Implement Member use cases with database persistence.
    
    The service applies application rules and defines transaction boundaries.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        # Share the factpry, but each operation creates it's own Session
        self._session_factory = session_factory

    def list_members(self) -> list[Member]:
        with self._session_factory() as session:
            return MemberRepository(session).list_all()        

    def get_member(self, member_id: int) -> Member:
        with self._session_factory() as session:
            member = MemberRepository(session).get_by_id(member_id)
            if member is None:
                raise MemberNotFoundError
            return member

    def create_member(self, data: MemberInput) -> Member:
        # begin() commits on success and rolls back if an exception escapes.
        with self._session_factory.begin() as session:
            try:
                member = MemberRepository(session).create(data)
            except IntegrityError as error:
                if error.orig.sqlstate == '23505' and error.orig.diag.constraint_name == 'uq_members_email':
                    raise EmailAlreadyExistsError
                elif error.orig.sqlstate == '23505' and error.orig.diag.constraint_name == 'uq_membership_id':
                    raise MembershipIdAlreadyExistsError
                raise
            session.refresh(member)
            return member

    def replace_member(self, member_id: int, data: MemberInput) -> Member:
        with self._session_factory.begin() as session:
            repository = MemberRepository(session)
            member = repository.get_by_id(member_id)
            if member is None:
                raise MemberNotFoundError
            try:
                updated_member = repository.replace(member, data)
            except IntegrityError as error:
                if error.orig.sqlstate == '23505' and error.orig.diag.constraint_name == 'uq_members_email':
                    raise EmailAlreadyExistsError
                elif error.orig.sqlstate == '23505' and error.orig.diag.constraint_name == 'uq_membership_id':
                    raise MembershipIdAlreadyExistsError
                raise
            session.refresh(updated_member)
            return updated_member

    def delete_member(self, member_id: int) -> None:
        with self._session_factory.begin() as session:
            repository = MemberRepository(session)
            member = repository.get_by_id(member_id)
            if member is None:
                raise MemberNotFoundError
            if BookRepository(session).exists_for_member(member_id):
                raise MemberHasBooksError
            repository.delete(member)

    def list_member_books(self, member_id: int) -> list[Book]:
        with self._session_factory() as session:
            if MemberRepository(session).get_by_id(member_id) is None:
                raise MemberNotFoundError
            return BookRepository(session).list_by_member(member_id)