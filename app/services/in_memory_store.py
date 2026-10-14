"""Shared in-memory state for the alternative service implementations."""

from dataclasses import dataclass, field
from threading import RLock

from app.models.member import Member
from app.models.book import Book

@dataclass
class InMemoryStore:
    """Hold Members and Books for one application-scoped in-memory service pair."""

    members: list[Member] = field(default_factory=list)
    books: list[Book] = field(default_factory=list)
    # One process-local lock protects compound operations such as:
    # ID generation, relationship checks, list mutation
    lock: RLock = field(default_factory=RLock, repr=False)