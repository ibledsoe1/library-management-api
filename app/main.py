"""FastAPI application for the Library Management API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models # This is here to register ORM models before create_all() runs I think
from app.config import Settings, StorageBackend
from app.models.base import Base
from app.database.session import create_database
from app.routers.members import router as members_router
from app.routers.books import router as books_router
from app.services.in_memory_store import InMemoryStore
from app.services.members import DatabaseMemberService, InMemoryMemberService
from app.services.books import DatabaseBookService, InMemoryBookService

# Tags for SwaggerUI and ReDoc
tags_metadata = [
    {
        "name": "General",
        "description": "Basic application information and health checks.",
    },
    {
        "name": "Members",
        "description": "Create and manage members and retrieve their books.",
    },
    {
        "name": "Books",
        "description": "Create and manage books that belong to members.",
    },
]

# Create missing tables at startup
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize application-scoped infrastructure at startup"""
    settings = Settings()
    application.state.settings = settings

    if settings.storage_backend is StorageBackend.MEMORY:
        store = InMemoryStore()
        application.state.member_service = InMemoryMemberService(store)
        application.state.book_service = InMemoryBookService(store)
    elif settings.storage_backend is StorageBackend.DATABASE:
        database = create_database(settings)
        Base.metadata.create_all(bind=database.engine)
        # Services are stateless, safe to share, 
        # they receive session factory, each DB operation
        # creates it's own unit of work and controls transaction
        application.state.member_service = DatabaseMemberService(
            database.session_factory
        )
        application.state.book_service = DatabaseBookService(
            database.session_factory
        )
    # code after yield would run during app shutdown
    yield

# Create FastApi app object for Uvicorn
# metadata displayed in generated API docs
app = FastAPI(
    title="Library Management API",
    description=(
        "Manage the members of the library and books."
        "This is for SDEV 3310 assignment 1"
    ),
    version="0.2.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(members_router)
app.include_router(books_router)


@app.get("/", tags=["General"], summary="Introduce the API")
def read_root() -> dict[str, str]:
    """Return a short introduction to the API."""
    return {"message": "Library Management API"}


@app.get("/health", tags=["General"], summary="Check API health")
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""
    return {"status": "healthy"}
