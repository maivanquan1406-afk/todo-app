# Todo List API - FastAPI Application

A comprehensive **8-level** Todo List API built with FastAPI, SQLModel, and JWT authentication. Features user authentication, deadline management, and complete test coverage.

## Features

### Cấp 0: Health Check
- `GET /health` - API health status
- `GET /` - Welcome message

### Cấp 1-4: Core CRUD Operations
- `POST /api/v1/todos/` - Create todo
- `GET /api/v1/todos/` - List todos with filtering, sorting, pagination
- `GET /api/v1/todos/{id}` - Get single todo
- `PATCH /api/v1/todos/{id}` - Update todo (partial)
- `PUT /api/v1/todos/{id}` - Update todo (full)
- `DELETE /api/v1/todos/{id}` - Delete todo
- `POST /api/v1/todos/{id}/complete` - Mark as complete

**Validation:**
- Title: 3-100 characters
- Supports filtering by search query, is_done status
- Sorting by created_at
- Pagination with limit/offset

### Cấp 5: User Authentication
- `POST /api/v1/auth/register` - Create new user account
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile

**Features:**
- JWT token-based authentication
- PBKDF2-SHA256 password hashing
- User isolation - each user sees only their todos

### Cấp 6: Deadline & Tag Management
- `due_date` field on todos (Optional ISO datetime)
- `tags` field on todos (Optional string)
- `GET /api/v1/todos/overdue` - Get overdue incomplete todos
- `GET /api/v1/todos/today` - Get today's incomplete todos

### Cấp 7: Testing & Containerization
- Comprehensive pytest test suite (21 tests)
  - 8 authentication tests
  - 13 todo CRUD and isolation tests
- Dockerfile - Multi-stage build
- docker-compose.yml - Docker Compose setup

## Quick Start

1. **Create and activate virtualenv:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run server:**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Run tests:**
   ```bash
   pytest -v
   ```

## Key Endpoints
http://127.0.0.1:8000/api/v1/auth/login-page
**Authentication:**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

**Todos:**
- `GET/POST /api/v1/todos/`
- `GET /api/v1/todos/{id}`
- `PATCH/PUT /api/v1/todos/{id}`
- `DELETE /api/v1/todos/{id}`
- `POST /api/v1/todos/{id}/complete`
- `GET /api/v1/todos/overdue` (Cấp 6)
- `GET /api/v1/todos/today` (Cấp 6)

## Docker Support

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
```

## Technology Stack

- **Framework:** FastAPI
- **ORM:** SQLModel (SQLAlchemy)
- **Database:** SQLite (PostgreSQL ready)
- **Auth:** JWT (python-jose)
- **Testing:** pytest + httpx
- **Containerization:** Docker + Docker Compose
- **Python:** 3.12+

## Project Structure

```
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── db.py                   # Database config
│   ├── models.py               # Data models
│   ├── core/
│   │   ├── config.py           # App config
│   │   └── jwt.py              # Auth utils
│   ├── repositories/           # Data access layer
│   ├── services/               # Business logic
│   └── routers/                # API endpoints
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth.py            # Auth tests (8)
│   └── test_todos.py           # Todos tests (13)
├── Dockerfile                  # Container image
├── docker-compose.yml          # Compose setup
└── requirements.txt            # Dependencies
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py
pytest tests/test_todos.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app tests/
```

## Example Usage

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

### Create Todo
```bash
curl -X POST http://localhost:8000/api/v1/todos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title": "Buy milk", "due_date": "2026-02-15T18:00:00", "tags": "shopping"}'
```

### Get Overdue
```bash
curl -X GET http://localhost:8000/api/v1/todos/overdue \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Status

✅ Cấp 0-7 Complete
- [x] Health endpoints
- [x] CRUD operations
- [x] Validation & filtering
- [x] Repository/Service/Router layering
- [x] SQLite + SQLModel
- [x] JWT authentication
- [x] Due dates & tags
- [x] Pytest tests
- [x] Docker support

📋 Cấp 8 (Ready):
- Soft delete implementation (schema prepared)

---

Version: 1.0.0
Built for Lec05 - Application Development Course
