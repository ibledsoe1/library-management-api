"""FastAPI application for the Library Management API."""

from fastapi import FastAPI

from app.routers.members import router as members_router
from app.routers.books import router as books_router

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

# Create FastApi app object for Uvicorn
# metadata displayed in generated API docs
app = FastAPI(
    title="Library Management API",
    description=(
        "Manage the members of the library and books."
        "This is for SDEV 3310 assignment 1"
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
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
