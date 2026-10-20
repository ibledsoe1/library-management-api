"""In-memory Member service implementation."""

from app.exceptions import MemberHasBooksError, MemberNotFoundError
from app.models.member import Member
from app.models.book import Book
from app.schemas.members import MemberInput
from app.services.in_memory_store import InMemoryStore
from .base import MemberService


class InMemoryMemberService(MemberService):
    """Implement Member use cases with shared in-memory state.

    Data is process-local and non-durable.
    """

    def __init__(self, store: InMemoryStore):
        self._store = store

    def list_members(self) -> list[Member]:
        with self._store.lock:
            return list(self._store.members)

    def get_member(self, member_id: int) -> Member:
        with self._store.lock:
            for member in self._store.members:
                if member.id == member_id:
                    return member
            raise MemberNotFoundError

    def create_member(self, data: MemberInput) -> Member:
        # Lock ID generation and append as one operation.
        with self._store.lock:
            member = Member(
                id=max((item.id for item in self._store.members), default=0) + 1,
                **data.model_dump(),
            )
            self._store.members.append(member)
            return member

    def replace_member(self, member_id: int, data: MemberInput) -> Member:
        with self._store.lock:
            member = self.get_member(member_id)
            member.name = data.name
            member.email = data.email
            member.membership_id = data.membership_id
            member.phone = data.phone
            return member

    def delete_member(self, member_id: int) -> None:
        with self._store.lock:
            member = self.get_member(member_id)
            if any(book.member_id == member_id for book in self._store.books):
                raise MemberHasBooksError
            self._store.members.remove(member)

    def list_member_books(self, member_id: int) -> list[Book]:
        with self._store.lock:
            self.get_member(member_id)
            return [
                book for book in self._store.books if book.member_id == member_id
            ]