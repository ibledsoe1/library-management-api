"""Unit tests for every Member Pydantic schema and declared rule."""

import pytest
from pydantic import ValidationError

from app.models.member import Member
from app.schemas.members import MemberInput, MemberResponse


@pytest.mark.parametrize("missing_field", ["name", "email", "membership_id", "phone"])
def test_member_create_requires_each_declared_field(missing_field: str) -> None:
    """A create request must include every Member field."""
    data = valid_member_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        MemberInput(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("name", "   "),
        ("name", "n" * 121),
        ("email", "not-an-email"),
        ("email", "missing-domain@"),
        ("phone", "123456789"),  # 9 digits
        ("phone", "12345678901"),  # 11 digits
        ("phone", "123-456-7890"),  # formatting characters are rejected
        ("phone", "abcdefghij"),
    ],
)
def test_member_create_enforces_field_boundaries(
    field_name: str,
    value: str,
) -> None:
    """Member fields must satisfy their declared constraints."""
    data = valid_member_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        MemberInput(**data)


def test_member_create_accepts_declared_maximum_length() -> None:
    """The inclusive maximum name length remains a valid request value."""
    data = valid_member_data()
    data["name"] = "n" * 120

    member = MemberInput(**data)

    assert len(member.name) == 120


def test_member_create_strips_surrounding_whitespace() -> None:
    """Shared schema configuration normalizes string input."""
    data = valid_member_data()
    data["name"] = "  Izzy Bledsoe  "
    data["membership_id"] = "  101  "
    data["phone"] = "  1234567890  "

    member = MemberInput(**data)

    assert member.name == "Izzy Bledsoe"
    assert member.membership_id == "101"
    assert member.phone == "1234567890"


def test_member_create_rejects_undocumented_field() -> None:
    """The request contract rejects input outside the documented schema."""
    with pytest.raises(ValidationError):
        MemberInput(**valid_member_data(), address="123 Main St")


def test_member_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Member field rules and configuration."""
    data = valid_member_data()
    data["name"] = "  Updated Member  "

    member = MemberInput(**data)

    assert member.name == "Updated Member"
    with pytest.raises(ValidationError):
        MemberInput(**{**data, "phone": "123"})


def test_member_response_reads_an_orm_member() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Member(id=1, **valid_member_data())

    # from_attributes=True lets Pydantic read attributes from a non-dict object.
    # FastAPI does this automatically for response_model, but a direct unit
    # test of the schema must request it.
    response = MemberResponse.model_validate(source, from_attributes=True)

    assert response.model_dump() == {**valid_member_data(), "id": 1}


def test_member_response_rejects_nonpositive_server_id() -> None:
    """A response must contain a positive server-generated identifier."""
    with pytest.raises(ValidationError):
        MemberResponse(**valid_member_data(), id=0)


# HELPERS


def valid_member_data() -> dict[str, str]:
    """Return a valid Member request body for focused validation scenarios."""
    return {
        "name": "Izzy Bledsoe",
        "email": "ibledsoe1@collin.edu",
        "membership_id": "101",
        "phone": "1234567890",
    }