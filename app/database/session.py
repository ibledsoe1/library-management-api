"""PostgreSQL engine and request-scoped SQLAlchemy sessions."""

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings

# frozen=True makes this read-only after creation
@dataclass(frozen=True)
class DatabaseInfrastructure:
    """Database engine and session factory created from validated settings."""

    engine: Engine
    session_factory: sessionmaker[Session]


def create_database(settings: Settings) -> DatabaseInfrastructure:
    """Create the engine and session factory for one application instance."""

    if settings.database_url is None:
        raise ValueError("DATABASE_URL is required to create database infrastructure")

    # The engine owns the connection pool, 
    # then sessions borrow connections from it only when DB work begins
    engine = create_engine(settings.database_url, echo=settings.database_echo_sql)

    # This factory creates a separate Session for each service operation
    # It's shared by services, but a Session is never shared between requests
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False
    )

    return DatabaseInfrastructure(engine=engine, session_factory=session_factory)

