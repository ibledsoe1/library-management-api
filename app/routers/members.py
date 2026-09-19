"""HTTP endpoints for the Member resource."""

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.members import MemberCreate, MemberResponse, MemberUpdate
from app.schemas.books import BookResponse
from app.storage import members, books

router = APIRouter(prefix="/members", tags=["Members"])


def find_member(member_id: int) -> MemberResponse:
    """Find one member or return an HTTP 404 error to the client."""
    for member in members:
        if member.id == member_id:
            return member

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )


# Return all library members
@router.get(
    "",
    response_model=list[MemberResponse],
    summary="List all members",
    description="Return every member currently stored by the application.",
)
def list_members() -> list[MemberResponse]:
    """Return every member currently stored in memory."""
    return members


# Return a specific member based on their member_id
@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get one member",
    description="Return the member identified by the path parameter.",
    responses={404: {"description": "Member not found"}},
)
def get_member(member_id: int) -> MemberResponse:
    """Return the member with the requested ID."""
    return find_member(member_id)


# Create a new member
@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
    description="Create a member from a validated name and description.",
)
def create_member(data: MemberCreate) -> MemberResponse:
    """Create a member from a validated JSON request body."""

    next_member_id = max((member.id for member in members), default=0) + 1
    member = MemberResponse(
        id=next_member_id,
        **data.model_dump(),
    )
    members.append(member)
    return member


# Replace/edit data for a specific member
@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Replace a member",
    description="Replace all editable fields of an existing member.",
    responses={404: {"description": "Member not found"}},
)
def replace_member(
    member_id: int,
    data: MemberUpdate,
) -> MemberResponse:
    """Replace the name and description of an existing member."""
    member = find_member(member_id)
    updated_member = MemberResponse(
        id=member_id,
        **data.model_dump(),
    )
    members[members.index(member)] = updated_member
    return updated_member


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
def delete_member(member_id: int) -> Response:
    """Remove a member from the in-memory collection."""
    member = find_member(member_id)

    # Do not leave Books pointing to a Member that no longer exists.
    if any(book.member_id == member_id for book in books):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete the member's books before deleting the member",
        )

    members.remove(member)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Get books checked out by a specific member
@router.get(
    "/{member_id}/books",
    response_model=list[BookResponse],
    summary="List a member's books",
    description="Return every book that belongs to the requested member.",
    responses={404: {"description": "Member not found"}},
)
def list_member_books(member_id: int) -> list[BookResponse]:
    """Return every book associated with the requested member."""
    find_member(member_id)
    return [book for book in books if book.member_id == member_id]
