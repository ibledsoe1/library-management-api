"""Predefined users and roles."""

from dataclasses import dataclass
from enum import Enum

from app.config import Settings

class Role(str, Enum):
    """Roles supported by the Library Management API permission policy."""

    MEMBER = "member"
    ADMIN = "admin"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represent the identity and role established by a valid Bearer token."""

    username: str
    role: Role


def get_token_for_role(role: Role, settings: Settings) -> str:
    """Return the validated token configured for one role."""
    if role is Role.MEMBER:
        return settings.member_token
    return settings.admin_token


def get_user_for_token(token: str, settings: Settings) -> AuthenticatedUser | None:
    """Map one configured token to its predefined user and role."""
    member_token = get_token_for_role(Role.MEMBER, settings)
    admin_token = get_token_for_role(Role.ADMIN, settings)

    # Empty environment values must not accidentally authenticate an empty credential
    # Empty string treated as unconfigured
    if member_token and token == member_token:
        return AuthenticatedUser(username="member", role=Role.MEMBER)
    if admin_token and token == admin_token:
        return AuthenticatedUser(username="admin", role=Role.ADMIN)
    return None