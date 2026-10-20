"""Database operations for Book records."""

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.books import BookInput


class BookRepository:
    """Read and write Book rows with a SQLAlchemy Session."""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> list[Book]:
        statement = select(Book).order_by(Book.id)
        return list(self.session.scalars(statement))

    def list_by_member(self, member_id: int) -> list[Book]:
        statement = (
            select(Book)
            .where(Book.member_id == member_id)
            .order_by(Book.id)
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, book_id: int) -> Book | None:
        return self.session.get(Book, book_id)

    def exists_for_member(self, member_id: int) -> bool:
        statement = select(exists().where(Book.member_id == member_id))
        return bool(self.session.scalar(statement))

    def create(self, data: BookInput) -> Book:
        book = Book(**data.model_dump())
        self.session.add(book)
        self.session.flush()
        return book

    def replace(self, book: Book, data: BookInput) -> Book:
        book.title = data.title
        book.author = data.author
        book.isbn = data.isbn
        book.published_year = data.published_year
        book.member_id = data.member_id
        self.session.flush()
        return book

    def delete(self, book: Book) -> None:
        self.session.delete(book)