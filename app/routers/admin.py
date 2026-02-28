from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.jwt import decode_token
from app.core.config import logger
from app.core.exceptions import AppError
from app.services.user_service import service as user_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _require_admin_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None, RedirectResponse("/api/v1/auth/login-page", status_code=302)

    email = decode_token(token)
    if not email:
        return None, RedirectResponse("/api/v1/auth/login-page", status_code=302)

    try:
        user = user_service.get_by_email(email)
    except AppError as exc:
        logger.error("Failed to fetch user for admin area", exc_info=True)
        return None, HTMLResponse("Internal server error", status_code=500)

    if not user:
        return None, RedirectResponse("/api/v1/auth/login-page", status_code=302)

    if user.role != "admin":
        return None, RedirectResponse("/dashboard", status_code=302)

    return user, None


@router.get("/users", response_class=HTMLResponse)
def list_users(request: Request, status: Optional[str] = None, error: Optional[str] = None):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    try:
        users = user_service.list_all()
    except AppError as exc:
        logger.error("Failed to list users", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": users,
            "current_user": admin_user,
            "status_message": status,
            "error_message": error,
        },
    )


@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, request: Request):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    if admin_user.id == user_id:
        return RedirectResponse("/admin/users?error=Bạn không thể xóa chính mình", status_code=303)

    try:
        deleted = user_service.delete_user(user_id)
    except AppError as exc:
        logger.error("Failed to delete user", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    if not deleted:
        return RedirectResponse("/admin/users?error=Người dùng không tồn tại", status_code=303)

    return RedirectResponse("/admin/users?status=Đã xóa người dùng", status_code=303)
