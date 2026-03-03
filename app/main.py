from __future__ import annotations

from fastapi import FastAPI, Request, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from datetime import datetime, date
from typing import Optional, Dict
import json
from json import JSONDecodeError
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv


class ForwardedProtoMiddleware:
    """Minimal ASGI middleware that respects X-Forwarded-* headers."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") in {"http", "websocket"}:
            proto = None
            host = None
            for key_bytes, value_bytes in scope.get("headers", []):
                key = key_bytes.decode("latin1").lower()
                value = value_bytes.decode("latin1")
                if key == "x-forwarded-proto" and not proto:
                    proto = value.split(",")[0].strip()
                elif key == "x-forwarded-host" and not host:
                    host = value.split(",")[0].strip()

            if proto or host:
                scope = dict(scope)
                if proto:
                    scope["scheme"] = proto
                if host:
                    hostname, _, forwarded_port = host.partition(":")
                    current_server = scope.get("server") or (hostname, None)
                    port = current_server[1]
                    if forwarded_port.isdigit():
                        port = int(forwarded_port)
                    elif port is None:
                        port = 443 if proto == "https" else 80
                    scope["server"] = (hostname, port)

        await self.app(scope, receive, send)

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=False)
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATE_DIR = BASE_DIR / "app" / "templates"

from app.routers import todos, auth, admin, password_reset_router
from app.db import init_db
from app.core.config import settings, logger
from app.core.jwt import decode_token
from app.services.user_service import service as user_service
from app.services.todo_service import service as todo_service
from app.services.reminder_service import reminder_scheduler
from app.models import TodoCreate, TodoUpdate
from app.core.exceptions import AppError
from pydantic import BaseModel, ValidationError as PydanticValidationError


# =======================
# Lifespan (startup/shutdown)
# =======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting")
    try:
        init_db()
        logger.info("Database initialized (env=%s)", settings.ENVIRONMENT)
        reminder_scheduler.start()
    except Exception:
        logger.exception("Database initialization failed")
    yield
    await reminder_scheduler.stop()
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_current_user_to_request(request: Request, call_next):
    request.state.current_user = None
    token = request.cookies.get("access_token")
    if token:
        email = decode_token(token)
        if email:
            try:
                request.state.current_user = user_service.get_by_email(email)
            except AppError:
                logger.warning("Unable to load current user for request", exc_info=True)
    response = await call_next(request)
    return response

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

# Respect X-Forwarded-* headers from Railway/other proxies so generated URLs stay on HTTPS
app.add_middleware(ForwardedProtoMiddleware)

# =======================
# Routers (API)
# =======================
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(password_reset_router.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1/todos", tags=["todos"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

# =======================
# Static & Templates
# =======================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


DEFAULT_TASK_META = {
    "priority": "medium",
    "category": "General",
    "status": "backlog",
    "reminder_minutes": settings.REMINDER_LEAD_MINUTES,
}
VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"backlog", "in_progress", "done"}


class StatusUpdatePayload(BaseModel):
    status: str
    priority: Optional[str] = None
    category: Optional[str] = None
    reminder_minutes: Optional[int] = None


def _resolve_dashboard_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    email = decode_token(token)
    if not email:
        return None
    try:
        user = user_service.get_by_email(email)
    except AppError:
        logger.error("Failed to resolve dashboard user", exc_info=True)
        return None
    return user


def _merge_task_meta(raw_tags: Optional[str], overrides: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    meta = DEFAULT_TASK_META.copy()
    if raw_tags:
        try:
            parsed = json.loads(raw_tags)
        except JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if value is not None:
                    meta[key] = value
    overrides = overrides or {}
    for key, value in overrides.items():
        if value:
            meta[key] = value
    return meta


def _normalize_reminder_minutes(value: Optional[int | str]) -> int:
    if value is None or value == "":
        return settings.REMINDER_LEAD_MINUTES
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return settings.REMINDER_LEAD_MINUTES
    minutes = max(1, minutes)
    minutes = min(minutes, settings.REMINDER_MAX_LEAD_MINUTES)
    return minutes


def _coerce_optional_reminder(value: Optional[int | str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None
    minutes = max(1, minutes)
    minutes = min(minutes, settings.REMINDER_MAX_LEAD_MINUTES)
    return minutes


def _safe_redirect_target(request: Request, fallback: str = "/dashboard") -> str:
    next_url = request.query_params.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return fallback


def _format_vietnamese_date(target_date: date) -> str:
    weekdays = [
        "Thứ 2",
        "Thứ 3",
        "Thứ 4",
        "Thứ 5",
        "Thứ 6",
        "Thứ 7",
        "Chủ nhật",
    ]
    weekday_label = weekdays[target_date.weekday()] if 0 <= target_date.weekday() < len(weekdays) else ""
    return f"{weekday_label}, {target_date.strftime('%d/%m/%Y')}"


def _build_todo_payload(todo) -> Dict[str, Optional[str]]:
    meta = _merge_task_meta(todo.tags)
    status = "done" if todo.is_done else meta.get("status", DEFAULT_TASK_META["status"])
    if todo.is_done:
        meta["status"] = "done"
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "is_done": todo.is_done,
        "due_date": todo.due_date.isoformat() if todo.due_date else None,
        "due_display": todo.due_date.strftime('%d/%m/%Y %H:%M') if todo.due_date else None,
        "priority": meta.get("priority", DEFAULT_TASK_META["priority"]),
        "category": meta.get("category", DEFAULT_TASK_META["category"]),
        "status": status,
    }


def _build_todo_collection(items):
    return [_build_todo_payload(todo) for todo in items]


def _parse_form_due_date(raw_due: Optional[str]) -> tuple[date, Optional[str], Optional[str]]:
    fallback_date = datetime.utcnow().date()
    if not raw_due:
        return fallback_date, None, None
    if "T" in raw_due:
        date_part, time_part = raw_due.split("T", 1)
    else:
        date_part, time_part = raw_due, None
    try:
        parsed_date = datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        parsed_date = fallback_date
    hour = minute = None
    if time_part and ":" in time_part:
        parts = time_part.split(":")
        hour = parts[0][:2]
        minute = parts[1][:2] if len(parts) > 1 else "00"
    return parsed_date, hour, minute


def _render_day_page(
    request: Request,
    user,
    selected_date: date,
    *,
    status_code: int = 200,
    form_error: Optional[str] = None,
    form_defaults: Optional[Dict[str, Optional[str]]] = None,
):
    try:
        todos_for_day = todo_service.get_by_date(user.id, selected_date)
    except AppError as exc:
        logger.error("Dashboard daily view failed", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    context = {
        "request": request,
        "user": user,
        "todos": _build_todo_collection(todos_for_day),
        "selected_date": selected_date,
        "selected_date_str": selected_date.strftime("%Y-%m-%d"),
        "selected_date_display": _format_vietnamese_date(selected_date),
        "form_error": form_error,
        "form_defaults": form_defaults or {},
        "default_reminder_minutes": settings.REMINDER_LEAD_MINUTES,
    }
    return templates.TemplateResponse("day_tasks.html", context, status_code=status_code)


def _handle_dashboard_validation_error(
    request: Request,
    user,
    *,
    title: str,
    description: Optional[str],
    due_date_raw: Optional[str],
    reminder_minutes: Optional[int | str],
    error_message: str,
):
    selected_date, hour, minute = _parse_form_due_date(due_date_raw)
    reminder_value = _normalize_reminder_minutes(reminder_minutes)
    form_defaults = {
        "title": title,
        "description": description or "",
        "hour": hour,
        "minute": minute,
        "reminder": reminder_value,
    }
    return _render_day_page(
        request,
        user,
        selected_date,
        status_code=400,
        form_error=error_message,
        form_defaults=form_defaults,
    )

# =======================
# Web pages
# =======================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = _resolve_dashboard_user(request)
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    try:
        todos_list, _ = todo_service.list(user.id, limit=100, offset=0)
    except AppError as exc:
        logger.error("Dashboard todo list failed", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    selected_date = request.query_params.get("date")
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "todos": todos_list,
            "prefill_date": selected_date,
            "today_str": datetime.utcnow().strftime("%Y-%m-%d"),
        }
    )


@app.get("/dashboard/day/{date_str}", response_class=HTMLResponse)
def dashboard_day_view(date_str: str, request: Request):
    user = _resolve_dashboard_user(request)
    if not user:
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return HTMLResponse("Ngày không hợp lệ", status_code=400)
    return _render_day_page(request, user, selected_date)


@app.post("/dashboard/todos")
def dashboard_create_todo(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    due_date: str = Form(None),
    reminder_minutes: Optional[str] = Form(None),
    priority: str = Form("medium"),
    category: str = Form("General"),
    status: str = Form("backlog"),
):
    expects_json = "application/json" in (request.headers.get("accept", "").lower())
    user = _resolve_dashboard_user(request)
    if not user:
        if expects_json:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    due_raw = due_date
    due = None
    if due_raw:
        try:
            due = datetime.fromisoformat(due_raw)
        except ValueError:
            pass

    priority_value = (priority or DEFAULT_TASK_META["priority"]).lower()
    if priority_value not in VALID_PRIORITIES:
        priority_value = DEFAULT_TASK_META["priority"]
    status_value = (status or DEFAULT_TASK_META["status"]).lower()
    if status_value not in VALID_STATUSES:
        status_value = DEFAULT_TASK_META["status"]
    reminder_value = _normalize_reminder_minutes(reminder_minutes)
    meta = _merge_task_meta(None, {
        "priority": priority_value,
        "category": category or DEFAULT_TASK_META["category"],
        "status": status_value,
        "reminder_minutes": reminder_value,
    })

    try:
        payload = TodoCreate(
            title=title,
            description=description,
            due_date=due,
            tags=json.dumps(meta)
        )
    except PydanticValidationError as exc:
        if expects_json:
            return JSONResponse({"error": "validation_error", "details": exc.errors()}, status_code=422)

        error_message = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại."
        for entry in exc.errors():
            loc = entry.get("loc") or []
            if "title" in loc:
                error_message = "Tên công việc phải có ít nhất 3 ký tự."
                break

        return _handle_dashboard_validation_error(
            request,
            user,
            title=title,
            description=description,
            due_date_raw=due_raw,
            reminder_minutes=reminder_value,
            error_message=error_message,
        )

    try:
        todo = todo_service.create(
            data=payload,
            owner_id=user.id
        )
    except AppError as exc:
        logger.error("Dashboard create todo failed", exc_info=True)
        if expects_json:
            return JSONResponse({"error": "failed_to_create"}, status_code=500)
        return HTMLResponse("Internal server error", status_code=500)

    if expects_json:
        return JSONResponse(_build_todo_payload(todo), status_code=201)
    return RedirectResponse(_safe_redirect_target(request), status_code=303)


@app.post("/dashboard/todos/{todo_id}/complete")
def dashboard_complete(todo_id: int, request: Request):
    expects_json = "application/json" in (request.headers.get("accept", "").lower())
    user = _resolve_dashboard_user(request)
    if not user:
        if expects_json:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    try:
        todo = todo_service.mark_complete(todo_id, user.id)
    except AppError as exc:
        logger.error("Dashboard mark complete failed", exc_info=True)
        if expects_json:
            return JSONResponse({"error": "failed"}, status_code=500)
        return HTMLResponse("Internal server error", status_code=500)
    if expects_json:
        return JSONResponse(_build_todo_payload(todo))
    return RedirectResponse(_safe_redirect_target(request), status_code=303)


@app.post("/dashboard/todos/{todo_id}/delete")
def dashboard_delete(todo_id: int, request: Request):
    expects_json = "application/json" in (request.headers.get("accept", "").lower())
    user = _resolve_dashboard_user(request)
    if not user:
        if expects_json:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/api/v1/auth/login-page", status_code=302)

    try:
        todo_service.delete(todo_id, user.id)
    except AppError as exc:
        logger.error("Dashboard delete todo failed", exc_info=True)
        if expects_json:
            return JSONResponse({"error": "failed"}, status_code=500)
        return HTMLResponse("Internal server error", status_code=500)
    if expects_json:
        return JSONResponse({"success": True})
    return RedirectResponse(_safe_redirect_target(request), status_code=303)


@app.post("/dashboard/todos/{todo_id}/status")
def dashboard_update_status(todo_id: int, request: Request, payload: StatusUpdatePayload = Body(...)):
    user = _resolve_dashboard_user(request)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        todo = todo_service.get(todo_id, user.id)
    except AppError as exc:
        logger.error("Dashboard status fetch failed", exc_info=True)
        return JSONResponse({"error": "not_found"}, status_code=404)

    requested_status = (payload.status or DEFAULT_TASK_META["status"]).lower()
    if requested_status not in VALID_STATUSES:
        requested_status = DEFAULT_TASK_META["status"]
    requested_priority = (payload.priority or DEFAULT_TASK_META["priority"]).lower()
    if requested_priority not in VALID_PRIORITIES:
        requested_priority = DEFAULT_TASK_META["priority"]
    overrides = {
        "status": requested_status,
        "priority": requested_priority,
        "category": payload.category or DEFAULT_TASK_META["category"],
    }
    reminder_override = _coerce_optional_reminder(payload.reminder_minutes)
    if reminder_override is not None:
        overrides["reminder_minutes"] = reminder_override
    meta = _merge_task_meta(todo.tags, overrides)

    update_payload = TodoUpdate(tags=json.dumps(meta))
    if requested_status == "done":
        update_payload.is_done = True
    else:
        update_payload.is_done = False

    try:
        updated = todo_service.update(todo_id, user.id, update_payload)
    except AppError as exc:
        logger.error("Dashboard status update failed", exc_info=True)
        return JSONResponse({"error": "update_failed"}, status_code=500)

    return JSONResponse(_build_todo_payload(updated))
