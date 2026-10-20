"""HTTP endpoints for the Book resource."""

from fastapi import APIRouter, HTTPException, Response, status, Depends

from app.depencencies import get_book_service
from app.exceptions import MemberNotFoundError, BookNotFoundError, ISBNAlreadyExistsError
from app.models.book import Book
from app.routers.http_errors import member_not_found, book_not_found, isbn_already_exists
from app.schemas.books import BookResponse, BookInput
from app.services.books import BookService

router = APIRouter(prefix="/books", tags=["Books"])
            
# Return all books
@router.get(
    "",
    response_model=list[BookResponse],
    summary="List all books",
    description="Return every book currently stored by the application.",
)
def list_books(service: BookService = Depends(get_book_service)) -> list[Book]:
    """Delegate Book retrieval to the service layer."""
    return service.list_books()


# Return a specific book based on its book_id
@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get one book",
    description="Return the book identified by the path parameter.",
    responses={404: {"description": "Book not found"}},
)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Return one Book or translate the missing-resource error."""
    try:
        return service.get_book(book_id)
    except BookNotFoundError:
        raise book_not_found() from None


# Create a new book
# To be created it needs to be associated with one existing member, 
# and it can't match an existing book's ISBN
@router.post(
    "",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
    description="Create a book and associate it with an existing member.",
    responses={
        404: {"description": "Related member not found"},
        409: {"description": "ISBN already in use"}
    },
)
def create_book(
    data: BookInput,
    service: BookService = Depends(get_book_service),
) -> Book:
    """Create a Book after the service verifies its business rules."""
    try:
        return service.create_book(data)
    except MemberNotFoundError:
        raise member_not_found() from None
    except ISBNAlreadyExistsError:
        raise isbn_already_exists() from None


# Replace/edit data for a specific book, including its member relationship
@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Replace a book",
    description="Replace all editable fields and verify the related member.",
    responses={
        404: {"description": "Book or related member not found"},
        409: {"description": "ISBN already in use"}
    },
)
def replace_book(
    book_id: int,
    data: BookInput,
    service: BookService = Depends(get_book_service),
) -> Book:
    """Replace a Book after checking both related resources."""
    try: 
        return service.replace_book(book_id, data)
    except BookNotFoundError:
        raise book_not_found() from None
    except MemberNotFoundError:
        raise member_not_found() from None
    except ISBNAlreadyExistsError:
        raise isbn_already_exists() from None


# Delete a specific book based on its book_id
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    description="Delete the book identified by the path parameter.",
    responses={404: {"description": "Book not found"}},
)
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> Response:
    """Delete a Book and translate the service outcome into HTTP."""
    try:
        service.delete_book(book_id)
    except BookNotFoundError:
        raise book_not_found() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
