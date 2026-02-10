from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.routers import todos, auth
from app.db import init_db
from app.core.config import settings
from app.core.jwt import decode_token
from app.services.user_service import service as user_service
from app.services.todo_service import service as todo_service
from fastapi import Form
from starlette.responses import RedirectResponse as StarletteRedirect
from app.models import TodoCreate
from datetime import datetime

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Add CORS middleware for Railway and other deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    print(f"Database initialized successfully (Environment: {settings.ENVIRONMENT})")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(todos.router, prefix="/api/v1/todos")

# Serve static files (css, js, images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        return RedirectResponse(url='/api/v1/auth/login-page')
    email = decode_token(token)
    if not email:
        return RedirectResponse(url='/api/v1/auth/login-page')
    user = user_service.get_by_email(email)
    if not user:
        return RedirectResponse(url='/api/v1/auth/login-page')
    items, total = todo_service.list(user.id, limit=100, offset=0)
    return templates.TemplateResponse('dashboard.html', {"request": request, "user": user, "todos": items})


@app.post('/dashboard/todos')
def dashboard_create_todo(request: Request, title: str = Form(...), description: str = Form(None), due_date: str = Form(None)):
    token = request.cookies.get('access_token')
    if not token:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    email = decode_token(token)
    if not email:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    user = user_service.get_by_email(email)
    if not user:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    # Create todo via service
    try:
        due = None
        if due_date:
            try:
                # Expecting input like 'YYYY-MM-DDTHH:MM' from datetime-local
                due = datetime.fromisoformat(due_date)
            except Exception:
                due = None
        todo_service.create(data=TodoCreate(title=title, description=description, due_date=due), owner_id=user.id)
    except Exception:
        pass
    return StarletteRedirect(url='/dashboard')


@app.post('/dashboard/todos/{todo_id}/complete')
def dashboard_complete_todo(request: Request, todo_id: int):
    token = request.cookies.get('access_token')
    if not token:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    email = decode_token(token)
    if not email:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    user = user_service.get_by_email(email)
    if not user:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    todo_service.mark_complete(todo_id, user.id)
    return StarletteRedirect(url='/dashboard')


@app.post('/dashboard/todos/{todo_id}/delete')
def dashboard_delete_todo(request: Request, todo_id: int):
    token = request.cookies.get('access_token')
    if not token:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    email = decode_token(token)
    if not email:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    user = user_service.get_by_email(email)
    if not user:
        return StarletteRedirect(url='/api/v1/auth/login-page')
    todo_service.delete(todo_id, user.id)
    return StarletteRedirect(url='/dashboard')

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

