"""HTTP endpoints for the Member resource."""

from fastapi import APIRouter, HTTPException, Response, status, Depends

from app.depencencies import get_member_service
from app.exceptions import MemberHasBooksError, MemberNotFoundError
from app.models.member import Member
from app.models.book import Book
from app.routers.http_errors import member_has_books, member_not_found
from app.schemas.members import MemberInput, MemberResponse
from app.schemas.books import BookResponse
from app.services.members import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


# NOTE: Old code, might need for service layer?
# Uses the server generated int ID, not the membership_id string
"""
def find_member(member_id: int) -> MemberResponse:
    for member in members:
        if member.id == member_id:
            return member

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )

def check_unique_email(email: EmailStr, exclude_member_id: int | None = None) -> None:
    for member in members:
        if member.id != exclude_member_id and member.email == email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

def check_unique_membership_id(membership_id: str, exclude_member_id: int | None = None) -> None:
    for member in members:
        if member.id != exclude_member_id and member.membership_id == membership_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership ID already in use")
"""
            
# Return all library members
@router.get(
    "",
    response_model=list[MemberResponse],
    summary="List all members",
    description="Return every member currently stored by the application.",
)
def list_members(
    service: MemberService = Depends(get_member_service),
) -> list[Member]:
    """Delegate Member retrieval to the service layer."""
    return service.list_members()


# Return a specific member based on their member_id
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get one member",
    description="Return the member identified by the path parameter.",
    responses={404: {"description": "Member not found"}},
)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> Member:
    """Return the member with the requested ID or translate the missing-resource error."""
    try:
        return service.get_member(member_id)
    except MemberNotFoundError:
        raise member_not_found() from None


# Create a new member
# A new member can't share same email or membership_id as an existing member
@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
    description="Create a member from a validated JSON request body.",
    responses={
        409: {"description": "Email or membership ID already in use."},
    }
)
def create_member(
    data: MemberInput,
    service: MemberService = Depends(get_member_service),
) -> Member:
    """Pass validated input to the business and persistence layers."""
    return service.create_member(data)


# Replace/edit data for a specific member
@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Replace a member",
    description="Replace all editable fields of an existing member.",
    responses={
        404: {"description": "Member not found"},
        409: {"description": "Email or membership ID already in use."},
    },
)
def replace_member(
    member_id: int,
    data: MemberInput,
    service: MemberService = Depends(get_member_service),
) -> Member:
    """Replace one Member through the service layer."""
    try:
        return service.replace_member(member_id, data)
    except MemberNotFoundError:
        raise member_not_found() from None
    

# Delete a specific library member based on their member_id (if they have no checked out books)
@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a member",
    description="Delete a member only when it has no related books.",
    responses={
        404: {"description": "Member not found"},
        409: {"description": "Member still has related books"},
    },
)
def delete_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> Response:
    """Translate Member deletion outcomes into HTTP responses."""
    try:
        service.delete_member(member_id)
    except MemberNotFoundError:
        raise member_not_found() from None
    except MemberHasBooksError:
        raise member_has_books() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Get books checked out by a specific member
@router.get(
    "/{member_id}/books",
    response_model=list[BookResponse],
    summary="List a member's books",
    description="Return every book that belongs to the requested member.",
    responses={404: {"description": "Member not found"}},
)
def list_member_books(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> list[Book]:
    """Return related Books after the service verifies the Member."""

    try:
        return service.list_member_books(member_id)
    except MemberNotFoundError:
        raise member_not_found() from None