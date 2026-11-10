"""Shared pytest fixtures for API integration tests.

Fixture dependency flow for an API integration test:
    database_client -> reset_database -> db_engine -> postgres_container

Fixture dependency flow for an in-memory API integration test:
    memory_client -> application lifespan -> InMemoryStore

Fixture dependency flow for a repository integration test:
    db_session -> reset_database -> db_engine -> postgres_container

Fixture lifetimes: 
    One `pytest` command
    └── one PostgreSQL container and one SQLAlchemy Engine
        ├── each repository test gets a fresh database state and explicit
        │   SQLAlchemy Session
        ├── each database API router test gets a fresh database state and
        │   TestClient; the application creates SQLAlchemy Sessions for each
        │   operation
        └── each memory API router test gets a fresh InMemoryStore and
            TestClient

The container and engine use `scope="session"`, so they are shared for the
complete pytest command. The database reset, SQLAlchemy Session, and both
TestClient fixtures use the default `scope="function"`, so each test function
starts with isolated state. These pytest fixture scopes are separate from the
SQLAlchemy `Session` object created for database work.
"""

import os
from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.textclient import TestClient
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start one disposable PostgreSQL database for the entire pytest session."""

    with PostgresContainer(
        "postgres:18",
        username="postgres",
        password="postgres",
        dbname="library_management_test",
        driver="psycopg"
    ) as container:
        # App connects to a temp DB rather than local development DB
        os.environ["DATABASE_URL"] = container.get_connection_url()

        # pauses fixture while every test that needs the session-scoped container runs,
        # Pytest resumes only after entire pytest command has finished
        yield container

    # Remove test-only environment value
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def db_engine(postgres_container: PostgresContainer) -> Engine:
    """Return the application engine configured for the temp container."""
    # Requesting postgres_container as a parameter forces pytest to complete that fixture first
    # So DATABASE_URL is set before these imports

    # Importing models registers Member and Book with Base.metadata before the
    # table fixture creates the schema in the temp DB
    from app import models # noqa: F401
    from app.config import Settings
    from app.database.session import create_database

    # Build same DB infrastructute as app, but with Testcontainers URL installed by fixture above
    return create_database(Settings()).engine


@pytest.fixture
# NOTE: ask what generator[none, none, none] is even for
def reset_database(db_engine: Engine) -> Generator[None, None, None]:
    """Give each integration test empty Member and Book tables."""
    from app.models.base import Base

    # Refresh tables for each test function
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    # Plain yield has no test value, just marks boundary between setup and cleanup
    yield

    Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def db_session(
    reset_database: None, db_engine: Engine
) -> Generator[Session, None, None]:
    """Provide one real SQLAlchemy Session for a repository integration test."""

    # Requesting reset_database ensures the Testcontainers database is ready
    # and empty before this real DB session is created
    session_factory = sessionmaker(bind=db_engine, autoflush=False)
    with session_factory() as session:
        # Give repository test a real SQLAlchemy Session
        yield session

        # rollback any uncommitted transaction before reset_database drops tables
        # if theres a database error
        session.rollback()


@pytest.fixture
def database_client(reset_database: None) -> Generator[TestClient, None, None]:
    """Provide a TestClient after the temp database is ready."""

    from app.main import app

    with TestClient(app) as test_client:
        # Entering this context starts FastAPI's lifespan function,
        # without starting live server
        yield test_client

    # Leaving this context closes TestClient and runs FastAPI lifespan cleanup


@pytest.fixture
def memory_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Provide a TestClient whose lifespan selects the in-memory services."""

    # Override values from env
    # removing DATABASE_URL makes it clear this test doesn't need PostgreSQL
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.main import app

    with TestClient(app) as test_client:
        # FastAPI's lifespan creates a fresh InMemoryStore for this client,
        # so Members and Books can't leak between memory router tests
        yield test_client
    






    