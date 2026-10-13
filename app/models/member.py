"""SQLAlchemy model for the members table."""

from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Member(Base):
    """Map Member objects to rows in the members table."""

    __tablename__ = "members"

    # Explicit constraint names tell the service layer which uniqueness
    # rule an IntegrityError violated instead of guessing from error text.
    __table_args__ = (
        UniqueConstraint("email", name="uq_members_email"),
        UniqueConstraint("membership_id", name="uq_membership_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    membership_id: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str] = mapped_column(nullable=False)

    books: Mapped[list[Book]] = relationship(back_populates="member")