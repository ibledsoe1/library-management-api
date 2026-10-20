"""FastAPI dependencies that expose application services to HTTP routes."""

from fastapi import Request

from app.services.members import MemberService
from app.services.books import BookService

def get_member_service(request: Request) -> MemberService:
    """Return the startup-related Member service."""
    return request.app.state.member_service

def get_book_service(request: Request) -> BookService:
    """Return the startup-selected Book service."""
    return request.app.state.book_service