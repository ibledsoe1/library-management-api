"""Unit tests for every Member Pydantic schema and declared rule."""

import pytest
from pydantic import ValidationError

from app.models.member import Member
from app.schemas.members import MemberInput, MemberResponse


@pytest.mark.parametrize("missing_field", ["name", "description"])
def test_member_create_requires_each_declared_field(missing_field: str) -> None:
    """A create request must include both Member fields."""
    data = valid_member_data()
    data.pop(missing_field)

    with pytest.raises(ValidationError):
        MemberInput(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("name", "   "),
        ("description", "   "),
        ("name", "n" * 101),
        ("description", "d" * 501),
    ],
)
def test_member_create_enforces_field_boundaries(
    field_name: str,
    value: str,
) -> None:
    """Member names and descriptions must satisfy their declared constraints."""
    data = valid_member_data()
    data[field_name] = value

    with pytest.raises(ValidationError):
        MemberInput(**data)


def test_member_create_accepts_declared_maximum_lengths() -> None:
    """The inclusive maximum lengths remain valid request values."""
    member = MemberInput(name="n" * 100, description="d" * 500)

    assert len(member.name) == 100
    assert len(member.description) == 500


def test_member_create_strips_surrounding_whitespace() -> None:
    """Shared schema configuration normalizes string input."""
    member = MemberInput(
        name="  Testing Module  ",
        description="  Add automated tests.  ",
    )

    assert member.name == "Testing Module"
    assert member.description == "Add automated tests."


def test_member_create_rejects_undocumented_field() -> None:
    """The request contract rejects input outside the documented schema."""
    with pytest.raises(ValidationError):
        MemberInput(**valid_member_data(), owner="Instructor")


def test_member_update_uses_the_same_request_contract() -> None:
    """A replacement request inherits Member field rules and configuration."""
    member = MemberInput(
        name="  Updated Module  ",
        description="  Replace every editable field.  ",
    )

    assert member.name == "Updated Module"
    assert member.description == "Replace every editable field."


def test_member_response_reads_an_orm_member() -> None:
    """The response schema serializes attributes from an ORM model instance."""
    source = Member(id=1, name="Course API", description="Course demonstration")

    response = MemberResponse.model_validate(source)

    assert response.model_dump() == {
        "name": "Course API",
        "description": "Course demonstration",
        "id": 1,
    }


def test_member_response_rejects_nonpositive_server_id() -> None:
    """A response must contain a positive server-generated identifier."""
    with pytest.raises(ValidationError):
        MemberResponse(**valid_member_data(), id=0)


# HELPERS


def valid_member_data() -> dict[str, str]:
    """Return a valid Member request body for focused validation scenarios."""
    return {"name": "Testing Module", "description": "Add schema unit tests."}