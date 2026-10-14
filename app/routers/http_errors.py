"""Translate application outcomes into HTTP responses for API routes."""

from fastapi import HTTPException, status

def member_not_found() -> HTTPException:
    """Retirn the HTTP 404 response for a missing Member.
    
    This mapping belongs in the router package because HTTPException is a
    FastAPI transport concern, not a business-rule concern.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found"
    )

def book_not_found() -> HTTPException:
    """Return the HTTP 404 response for a missing Book."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found"
    )

def member_has_books() -> HTTPException:
    """Return the HTTP 409 response for a Member with related Books"""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Delete the member's books before deleting the member"
    )