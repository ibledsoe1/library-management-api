# Library Management API

This is a simple library management API, which lets users manage library related data such as Members and Books. Users can create, view, update, and delete Members or Books, and each Book belongs to a Member. 

This is for SDEV 3310 Assignment 1.

## Requirements

- [uv](https://docs.astral.sh/uv/)

`uv` manages the Python version, virtual environment, and member dependencies.

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

### Set up the member

From the repository root, run:

```bash
uv sync
```

If the required Python version is unavailable, `uv sync` downloads it. It also creates the virtual environment and installs the dependencies recorded in `uv.lock`.

## Run the API

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
    "phone":"1231231234",
    "id":2
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
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── books.py
│   │   └── members.py
│   ├── __init__.py
│   ├── main.py
│   └── storage.py
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
└── uv.lock
```