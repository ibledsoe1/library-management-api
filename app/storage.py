"""Temporary in-memory storage shared by the API routers."""

from app.schemas.members import MemberResponse
from app.schemas.books import BookResponse

members: list[MemberResponse] = [
    MemberResponse(
        id=1,
        name="Izzy Bledsoe",
        email="ibledsoe1@collin.edu",
        membership_id="101",
        phone="111-222-3333",
    )
]

books: list[BookResponse] = [
    BookResponse(
        id=1,
        title="The Fellowship Of The Ring",
        author="J.R.R. Tolkien",
        isbn="978-0547928210",
        published_year="2012",
        member_id=1
    )
]
