Quick start

1. Create and activate virtualenv

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run app:

```bash
uvicorn app.main:app --reload --port 8000
```

API endpoints:
- GET /health
- GET / -> welcome message
- GET /api/v1/todos
- POST /api/v1/todos
- GET /api/v1/todos/{id}
- PUT/PATCH/DELETE /api/v1/todos/{id}
- POST /api/v1/todos/{id}/complete
