from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from datetime import datetime
from contextlib import asynccontextmanager

from app.routers import todos, auth
from app.db import init_db
from app.core.config import settings
from app.core.jwt import decode_token
from app.services.user_service import service as user_service
from app.services.todo_service import service as todo_service
from app.models import TodoCreate


# =======================
# Lifespan (startup/shutdown)
# =======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("🚀 Application Starting...")
    try:
        init_db()
        print(f"✅ Database initialized (ENV={settings.ENVIRONMENT})")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
    print("=" * 50)
    yield
    print("🛑 Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Simple health check before any middleware
@app.get("/health", response_class=HTMLResponse)
def health():
    return "<h1>OK</h1>"

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <h1>{settings.APP_NAME}</h1>
    <p>Status: OK</p>
    <p>Environment: {settings.ENVIRONMENT}</p>
    """

# =======================
# CORS
# =======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production nên giới hạn domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# Routers (API)
# =======================
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(todos.router, prefix="/api/v1/todos", tags=["todos"])

# =======================
# Static & Templates
# =======================
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# =======================
# Web pages
# =======================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    email = decode_token(token)
    if not email:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    user = user_service.get_by_email(email)
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    todos_list, _ = todo_service.list(user.id, limit=100, offset=0)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "todos": todos_list
        }
    )


@app.post("/dashboard/todos")
def dashboard_create_todo(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None)
):
    token = request.cookies.get("access_token")
    email = decode_token(token) if token else None
    user = user_service.get_by_email(email) if email else None
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    due = None
    if due_date:
        try:
            due = datetime.fromisoformat(due_date)
        except ValueError:
            pass

    todo_service.create(
        data=TodoCreate(
            title=title,
            description=description,
            due_date=due
        ),
        owner_id=user.id
    )

    return RedirectResponse("/dashboard", status_code=303)


@app.post("/dashboard/todos/{todo_id}/complete")
def dashboard_complete(todo_id: int, request: Request):
    token = request.cookies.get("access_token")
    email = decode_token(token) if token else None
    user = user_service.get_by_email(email) if email else None
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    todo_service.mark_complete(todo_id, user.id)
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/dashboard/todos/{todo_id}/delete")
def dashboard_delete(todo_id: int, request: Request):
    token = request.cookies.get("access_token")
    email = decode_token(token) if token else None
    user = user_service.get_by_email(email) if email else None
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    todo_service.delete(todo_id, user.id)
    return RedirectResponse("/dashboard", status_code=303)
