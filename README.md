# Library Management API

This is a simple library management API, which lets users manage library related data such as Members and Books. Users can create, view, update, and delete Members or Books, and each Book belongs to a Member. 

This API uses layered architecture, and the storage type can be switched between in-memory and database. The default storage type is PostgreSQL database. To switch storage type to memory, set STORAGE_BACKEND=memory in .env to run the application with process-local lists. Changing it to STORAGE_BACKEND=database switches it back to the PostgreSQL database.

A Bearer token establishes identity, the identity role determines whether a request may read or changes resources. This API uses environment-configured tokens for the assignment. There is no user database, password login, OAuth provider,JWT issuance,refresh tokens, or token revocation.

This is for SDEV 3310 Assignment 3.

## Requirements

- [uv](https://docs.astral.sh/uv/)

`uv` manages the Python version, virtual environment, and dependencies.

### Install uv

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal, then verify the installation:

```bash
uv --version
```

### Set up PostgreSQL

Download the PostgreSQL installer (https://www.postgresql.org/download/) for your system and follow the installation instructions.

From the library-management-api folder, run the database setup script and enter the password.
```bash
psql -U postgres -d postgres -f scripts/setup_database.sql
```

### Install dependencies

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run automated tests

If Docker Desktop is not installed and running, follow the Docker Desktop setup instructions for your operating system: [Windows](docs/windows-setup.md#6-install-docker-desktop-for-automated-testing) or [macOS](docs/macos-setup.md#6-install-docker-desktop-for-automated-testing).

The test suite has three complementary levels:

- **Unit tests** isolate business rules; some use mocked database collaborators, and others use the in-memory services. They do not use HTTP or PostgreSQL.
- **Database integration tests** use `TestClient` to send requests through the API and use a temporary PostgreSQL database. Memory router integration tests use the same application boundary without PostgreSQL.
- **Conformance tests** check the generated OpenAPI contract, representative client-visible responses, and invalid requests.

Before running integration or conformance tests, start Docker Desktop. Testcontainers uses Docker Desktop to start a disposable PostgreSQL container automatically. The container is created for the pytest session and removed when the test run finishes. It is never the local development database.

Run all tests from the repository root:

```bash
uv run pytest
```

The first run may take longer while Docker downloads the PostgreSQL image. Test data is reset before each integration test, so one test does not affect another.

```text
pytest
  -> Testcontainers starts temporary PostgreSQL
  -> TestClient sends API requests
  -> pytest checks the responses
  -> Testcontainers removes PostgreSQL
```


## Run the API

Before starting the API, copy the sample environment file:

```bash
cp .env.example .env
```

The local connection uses the database user account and password created by the database setup script:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/library
```

The URL identifies the database dialect and driver, username, password, host, port, and database name. The `postgres:postgres` username and password are intentionally simple for the demo.


There are also two environment configured example tokens for this assignment:
```
MEMBER_TOKEN=member-token
ADMIN_TOKEN=admin-token
```
They are for demonstrating request flow only as an example of how tokens work. In reality they would be more complex than this and would be kept secret.


```bash
uv run uvicorn app.main:app --reload
```

- FastAPI defines routes and handles API requests.
- Uvicorn listens for HTTP connections and passes requests to FastAPI.
- `uv` manages the Python environment and runs the installed command.
- `--reload` restarts the development server after source-code changes.

The development server will be available at `http://localhost:8000`.

## Explore the API

The application exposes three views of the same OpenAPI contract:

- `http://localhost:8000/docs` — Swagger UI for exploring and calling endpoints
- `http://localhost:8000/redoc` — ReDoc for reading reference documentation
- `http://localhost:8000/openapi.json` — the machine-readable OpenAPI document

In docs, select "Authorize", and enter a token. Swagger UI adds the Authorization: Bearer ... header to protected requests.

- member-token can use the protected `GET` endpoints.
- admin-token can use all protected `GET`, `POST`, `PUT`, and `DELETE` endpoints.

Requests without a valid token receive `401 Unauthorized`. A valid member token on a write endpoint receives `403 Forbidden`.

| Method | URL | CRUD operation | Successful status |
|---|---|---|---|
| `GET` | `/` | Introduce the API | `200 OK` |
| `GET` | `/health` | Check API health | `200 OK` |
| `GET` | `/members` | List all Members | `200 OK` |
| `GET` | `/members/{member_id}` | Get one Member | `200 OK` |
| `POST` | `/members` | Create a Member | `201 Created` |
| `PUT` | `/members/{member_id}` | Replace a Member | `200 OK` |
| `DELETE` | `/members/{member_id}` | Delete a Member | `204 No Content` |
| `GET` | `/members/{member_id}/books` | List a Member's Books | `200 OK` |
| `GET` | `/books` | List all Books | `200 OK` |
| `GET` | `/books/{book_id}` | Get one Book | `200 OK` |
| `POST` | `/books` | Create a Book | `201 Created` |
| `PUT` | `/books/{book_id}` | Replace a Book | `200 OK` |
| `DELETE` | `/books/{book_id}` | Delete a Book | `204 No Content` |

Here's some example data you can use for Member `POST` and `PUT` requests:

```json
{
    "name":"John Doe",
    "email":"jdoe1@gmail.com",
    "membership_id":"102",
    "phone":"1231231234"
}
```

Member creation validation rules include:
- `name` is required and must be 1-120 characters.
- `email` is required and must be unique. It must be a valid email (has an @).
- `membership_id` is required and must be unique.
- `phone` is required. It must be a valid phone number that has 10 digits (Numbers only, no formatting such as dashes or parentheses).
- Surrounding whitespace is removed before validation.
- Unexpected fields are rejected.

Here's some example data you can use for Book `POST` and `PUT` requests.

```json
{
    "title":"The Hobbit",
    "author":"J.R.R Tolkien",
    "isbn":"978-0547928227",
    "published_year":2012,
    "member_id": 2
}
```

The `member_id` establishes the relationship between a Book and its Member.

Book validation rules include:
- `title` is required and must be 1-200 characters.
- `author` is required and must be 1-120 characters.
- `isbn` is required and must be unique.
- `published_year` must be between 1450 and the current year.
- `member_id` is required.
- Surrounding whitespace is removed before validation.
- Unexpected fields are rejected.

## Current project structure
```text
library-management-api/
├── app/
│   ├── auth/
│   │   ├── dependencies.py
│   │   └── users.py
│   ├── database/
│   │   └── session.py
│   ├── config.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── base.py
│   │   ├── member.py
│   │   └── book.py
│   ├── repositories/
│   │   ├── members.py
│   │   └── books.py
│   ├── routers/
│   │   ├── members.py
│   │   └── books.py
│   ├── schemas/
│   │   ├── members.py
│   │   └── books.py
│   ├── services/
│   │   ├── in_memory_store.py
│   │   ├── members/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── database.py
│   │   │   └── in_memory.py
│   │   └── books/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── database.py
│   │       └── in_memory.py
│   ├── exceptions.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── conformance/
│   │   ├── test_authentication_authorization_contract.py
│   │   ├── test_negative_requests.py
│   │   └── test_openapi_contract.py
│   ├── integration/
│   │   ├── repositories/
│   │   └── routers/
│   │       ├── database/
│   │       │   ├── test_projects.py
│   │       │   └── test_tasks.py
│   │       └── memory/
│   │           ├── test_projects.py
│   │           └── test_tasks.py
├── .env.example
├── pyproject.toml
└── README.md
```