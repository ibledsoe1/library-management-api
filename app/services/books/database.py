"""Relational-database Book service implementation."""

from sqlalchemy.orm import Session, sessionmaker

from app.exceptions import MemberNotFoundError, BookNotFoundError
from app.models.book import Book
from app.repositories.members import MemberRepository
from app.repositories.books import BookRepository
from app.schemas.books import BookInput
from .base import BookService


class DatabaseBookService(BookService):
    """Implement Book use cases with database persistence.

    The service applies application rules and defines transaction boundaries.
    """

    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def list_books(self) -> list[Book]:
        with self._session_factory() as session:
            return BookRepository(session).list_all()

    def get_book(self, book_id: int) -> Book:
        with self._session_factory() as session:
            book = BookRepository(session).get_by_id(book_id)
            if book is None:
                raise BookNotFoundError
            return book

    def create_book(self, data: BookInput) -> Book:
        # Verify the parent and insert the child atomically.
        with self._session_factory.begin() as session:
            if MemberRepository(session).get_by_id(data.member_id) is None:
                raise MemberNotFoundError
            book = BookRepository(session).create(data)
            session.refresh(book)
            return book

    def replace_book(self, book_id: int, data: BookInput) -> Book:
        # Lookup, validation, update, and commit are one atomic use case.
        with self._session_factory.begin() as session:
            book_repository = BookRepository(session)
            book = book_repository.get_by_id(book_id)
            if book is None:
                raise BookNotFoundError
            if MemberRepository(session).get_by_id(data.member_id) is None:
                raise MemberNotFoundError
            updated_book = book_repository.replace(book, data)
            session.refresh(updated_book)
            return updated_book

    def delete_book(self, book_id: int) -> None:
        with self._session_factory.begin() as session:
            book_repository = BookRepository(session)
            book = book_repository.get_by_id(book_id)
            if book is None:
                raise BookNotFoundError
            book_repository.delete(book)