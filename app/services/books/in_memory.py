"""In-memory Book service implementation."""

from app.exceptions import MemberNotFoundError, BookNotFoundError, ISBNAlreadyExistsError
from app.models.book import Book
from app.schemas.books import BookInput
from app.services.in_memory_store import InMemoryStore
from .base import BookService


class InMemoryBookService(BookService):
    """Implement Book use cases with shared in-memory state.

    Data is process-local and non-durable.
    """

    def __init__(self, store: InMemoryStore):
        self._store = store

    def list_books(self) -> list[Book]:
        with self._store.lock:
            return list(self._store.books)

    def get_book(self, book_id: int) -> Book:
        with self._store.lock:
            for book in self._store.books:
                if book.id == book_id:
                    return book
            raise BookNotFoundError

    def create_book(self, data: BookInput) -> Book:
        # Validate, generate the ID, and append while holding the lock.
        with self._store.lock:
            if not any(
                member.id == data.member_id for member in self._store.members
            ):
                raise MemberNotFoundError
            if any(
                book.isbn == data.isbn for book in self._store.books
            ):
                raise ISBNAlreadyExistsError
            book = Book(
                id=max((item.id for item in self._store.books), default=0) + 1,
                **data.model_dump(),
            )
            self._store.books.append(book)
            return book

    def replace_book(self, book_id: int, data: BookInput) -> Book:
        with self._store.lock:
            book = self.get_book(book_id)
            if not any(
                member.id == data.member_id for member in self._store.members
            ):
                raise MemberNotFoundError
            if any(
                book.isbn == data.isbn and book.id != book_id for book in self._store.books
            ):
                raise ISBNAlreadyExistsError
            book.title = data.title
            book.author = data.author
            book.isbn = data.isbn
            book.published_year = data.published_year
            book.member_id = data.member_id
            return book

    def delete_book(self, book_id: int) -> None:
        with self._store.lock:
            self._store.books.remove(self.get_book(book_id))