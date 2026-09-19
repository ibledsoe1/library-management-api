"""HTTP endpoints for the Book resource."""

from fastapi import APIRouter, HTTPException, Response, status

from app.routers.members import find_member
from app.schemas.books import BookCreate, BookResponse, BookUpdate
from app.storage import books

router = APIRouter(prefix="/books", tags=["Books"])


def find_book(book_id: int) -> BookResponse:
    """Find one book or return an HTTP 404 error to the client."""
    for book in books:
        if book.id == book_id:
            return book

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found",
    )


# Return all books
@router.get(
    "",
    response_model=list[BookResponse],
    summary="List all books",
    description="Return every book currently stored by the application.",
)
def list_books() -> list[BookResponse]:
    """Return every book currently stored in memory."""
    return books


# Return a specific book based on its book_id
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get one book",
    description="Return the book identified by the path parameter.",
    responses={404: {"description": "Book not found"}},
)
def get_book(book_id: int) -> BookResponse:
    """Return the book with the requested ID."""
    return find_book(book_id)


# Create a new book
# To be created it needs to be associated with one existing member
@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
    description="Create a book and associate it with an existing member.",
    responses={404: {"description": "Related member not found"}},
)
def create_book(data: BookCreate) -> BookResponse:
    """Create a book associated with an existing member."""

    find_member(data.member_id)
    next_book_id = max((book.id for book in books), default=0) + 1

    book = BookResponse(
        id=next_book_id,
        **data.model_dump(),
    )
    books.append(book)
    return book


# Replace/edit data for a specific book, including its member relationship
@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Replace a book",
    description="Replace all editable fields and verify the related member.",
    responses={
        404: {"description": "Book or related member not found"},
    },
)
def replace_book(
    book_id: int,
    data: BookUpdate,
) -> BookResponse:
    """Replace an existing book after checking its related member."""
    book = find_book(book_id)
    find_member(data.member_id)
    updated_book = BookResponse(
        id=book_id,
        **data.model_dump(),
    )
    books[books.index(book)] = updated_book
    return updated_book


# Delete a specific book based on its book_id
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete the book identified by the path parameter.",
    responses={404: {"description": "Book not found"}},
)
def delete_book(book_id: int) -> Response:
    """Remove a book from the in-memory collection."""
    book = find_book(book_id)
    books.remove(book)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
