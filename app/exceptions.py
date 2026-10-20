"""Application outcomes raised by services without depending on FastAPI."""

class MemberNotFoundError(Exception):
    """Signal that the requested Member does not exist.
    
    This exception remains outside the router package so the service can be
    reused by HTTP routes, jobs, or messages consumers without importing FastAPI
    """


class BookNotFoundError(Exception):
    """Signal that the requested Book does not exist."""


class MemberHasBooksError(Exception):
    """Signal that a Member cannot be deleted while Books reference it."""

class ISBNAlreadyExistsError(Exception):
    """Signal that an existing Book already has the entered ISBN."""

class EmailAlreadyExistsError(Exception):
    """Signal that an existing Member already has the entered email."""

class MembershipIdAlreadyExistsError(Exception):
    """Signal that an existing Member already has the entered membership id."""