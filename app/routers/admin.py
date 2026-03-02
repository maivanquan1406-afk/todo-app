from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.jwt import decode_token
from app.core.config import logger
from app.core.exceptions import AppError, ValidationError
from app.services.user_service import service as user_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


DATE_FORMAT = "%Y-%m-%d"
VIETNAM_TZ = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")


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


def _parse_date(value: Optional[str], *, end_of_day: bool = False) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError("Định dạng ngày phải là YYYY-MM-DD")
    if end_of_day:
        parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)
    localized = parsed.replace(tzinfo=VIETNAM_TZ)
    utc_value = localized.astimezone(timezone.utc)
    return utc_value


def _to_vietnam_time(value: Optional[datetime]) -> Optional[datetime]:
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(VIETNAM_TZ)


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    status: Optional[str] = None,
    error: Optional[str] = None,
    q: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    normalized_query = (q or "").strip()
    has_filter = bool(normalized_query or start_date or end_date)

    try:
        start = _parse_date(start_date) if start_date else None
        end = _parse_date(end_date, end_of_day=True) if end_date else None
        users = user_service.list_all()
        deleted_users = user_service.list_deleted()
        filtered_active_users = users
        filtered_deleted_users = deleted_users
        if has_filter:
            filtered_active_users = user_service.list_all(
                search=normalized_query or None,
                start_date=start,
                end_date=end,
            )
            filtered_deleted_users = user_service.list_deleted(
                search=normalized_query or None,
                start_date=start,
                end_date=end,
            )
    except ValidationError as exc:
        return RedirectResponse(
            f"/admin/users?error={exc}&q={q or ''}&start_date={start_date or ''}&end_date={end_date or ''}",
            status_code=303,
        )
    except AppError as exc:
        logger.error("Failed to list users", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    if request.headers.get("accept", "").lower().startswith("application/json"):
        payload = []
        deleted_payload = []
        for user in users:
            created_vn = _to_vietnam_time(user.created_at)
            utc_iso = None
            if user.created_at:
                normalized = user.created_at
                if normalized.tzinfo is None:
                    normalized = normalized.replace(tzinfo=timezone.utc)
                normalized = normalized.astimezone(timezone.utc)
                utc_iso = normalized.isoformat(timespec="milliseconds")
            payload.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "created_at": utc_iso,
                    "created_at_vietnam": created_vn.strftime("%d/%m/%Y %H:%M") if created_vn else None,
                }
            )
        for user in deleted_users:
            created_vn = _to_vietnam_time(user.created_at)
            deleted_vn = _to_vietnam_time(user.deleted_at)
            normalized_created = None
            if user.created_at:
                normalized_created = user.created_at
                if normalized_created.tzinfo is None:
                    normalized_created = normalized_created.replace(tzinfo=timezone.utc)
                normalized_created = normalized_created.astimezone(timezone.utc)
            normalized_deleted = None
            if user.deleted_at:
                normalized_deleted = user.deleted_at
                if normalized_deleted.tzinfo is None:
                    normalized_deleted = normalized_deleted.replace(tzinfo=timezone.utc)
                normalized_deleted = normalized_deleted.astimezone(timezone.utc)
            deleted_payload.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "created_at": normalized_created.isoformat(timespec="milliseconds") if normalized_created else None,
                    "created_at_vietnam": created_vn.strftime("%d/%m/%Y %H:%M") if created_vn else None,
                    "deleted_at": normalized_deleted.isoformat(timespec="milliseconds") if normalized_deleted else None,
                    "deleted_at_vietnam": deleted_vn.strftime("%d/%m/%Y %H:%M") if deleted_vn else None,
                }
            )
        return JSONResponse({"users": payload, "deleted_users": deleted_payload})

    rendered_users = []
    rendered_deleted = []
    for user in users:
        created_vn = _to_vietnam_time(user.created_at)
        created_iso = None
        if user.created_at:
            normalized = user.created_at
            if normalized.tzinfo is None:
                normalized = normalized.replace(tzinfo=timezone.utc)
            normalized = normalized.astimezone(timezone.utc)
            created_iso = normalized.isoformat(timespec="milliseconds")
        rendered_users.append(
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "created_at_display": created_vn.strftime("%d/%m/%Y %H:%M") if created_vn else "-",
                "created_at_iso": created_iso,
            }
        )

    for user in deleted_users:
        created_vn = _to_vietnam_time(user.created_at)
        deleted_vn = _to_vietnam_time(user.deleted_at)
        created_iso = None
        deleted_iso = None
        if user.created_at:
            normalized = user.created_at
            if normalized.tzinfo is None:
                normalized = normalized.replace(tzinfo=timezone.utc)
            normalized = normalized.astimezone(timezone.utc)
            created_iso = normalized.isoformat(timespec="milliseconds")
        if user.deleted_at:
            normalized_del = user.deleted_at
            if normalized_del.tzinfo is None:
                normalized_del = normalized_del.replace(tzinfo=timezone.utc)
            normalized_del = normalized_del.astimezone(timezone.utc)
            deleted_iso = normalized_del.isoformat(timespec="milliseconds")
        rendered_deleted.append(
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "created_at_display": created_vn.strftime("%d/%m/%Y %H:%M") if created_vn else "-",
                "created_at_iso": created_iso,
                "deleted_at_display": deleted_vn.strftime("%d/%m/%Y %H:%M") if deleted_vn else "-",
                "deleted_at_iso": deleted_iso,
            }
        )

    def _format_created_display_value(value: Optional[datetime]) -> str:
        localized = _to_vietnam_time(value)
        return localized.strftime("%d/%m/%Y %H:%M") if localized else "-"

    filter_users_details = []
    for user in filtered_active_users:
        filter_users_details.append(
            {
                "email": user.email,
                "created_at_display": _format_created_display_value(user.created_at),
                "status": "active",
            }
        )
    for user in filtered_deleted_users:
        filter_users_details.append(
            {
                "email": user.email,
                "created_at_display": _format_created_display_value(user.created_at),
                "status": "deleted",
            }
        )

    return templates.TemplateResponse(
        "admin_users.html",
        {
            "request": request,
            "users": rendered_users,
            "deleted_users": rendered_deleted,
            "current_user": admin_user,
            "status_message": status,
            "error_message": error,
            "search_query": q or "",
            "start_date": start_date or "",
            "end_date": end_date or "",
            "filter_total_users": len(filtered_active_users) + len(filtered_deleted_users),
            "filter_users_details": filter_users_details,
        },
    )


@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, request: Request):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    wants_json = "application/json" in (request.headers.get("accept", "").lower())

    if admin_user.id == user_id:
        if wants_json:
            return JSONResponse({"status": "error", "message": "Bạn không thể xóa chính mình"}, status_code=400)
        return RedirectResponse("/admin/users?error=Bạn không thể xóa chính mình", status_code=303)

    try:
        deleted = user_service.delete_user(user_id)
    except AppError as exc:
        logger.error("Failed to delete user", exc_info=True)
        if wants_json:
            return JSONResponse({"status": "error", "message": "Không thể xóa người dùng"}, status_code=500)
        return HTMLResponse("Internal server error", status_code=500)

    if not deleted:
        if wants_json:
            return JSONResponse({"status": "error", "message": "Người dùng không tồn tại"}, status_code=404)
        return RedirectResponse("/admin/users?error=Người dùng không tồn tại", status_code=303)

    if wants_json:
        return JSONResponse({"status": "ok"})

    return RedirectResponse("/admin/users?status=Đã xóa người dùng", status_code=303)


@router.post("/users/delete-by-date")
def delete_users_by_date(
    request: Request,
    start_date: Optional[str] = Form(default=None),
    end_date: Optional[str] = Form(default=None),
):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    if not start_date and not end_date:
        return RedirectResponse("/admin/users?error=Vui lòng chọn ít nhất một ngày", status_code=303)

    try:
        start = _parse_date(start_date) if start_date else None
        end = _parse_date(end_date, end_of_day=True) if end_date else None
    except ValidationError as exc:
        return RedirectResponse(f"/admin/users?error={exc}", status_code=303)

    try:
        deleted = user_service.delete_users_by_date_range(start, end, exclude_ids=[admin_user.id])
    except AppError:
        logger.error("Failed bulk delete users", exc_info=True)
        return HTMLResponse("Internal server error", status_code=500)

    if deleted == 0:
        return RedirectResponse("/admin/users?status=Không có người dùng nào bị xóa", status_code=303)
    return RedirectResponse(f"/admin/users?status=Đã xóa {deleted} người dùng", status_code=303)


@router.post("/users/{user_id}/restore")
def restore_user(user_id: int, request: Request):
    admin_user, response = _require_admin_user(request)
    if response:
        return response

    wants_json = "application/json" in (request.headers.get("accept", "").lower())

    try:
        restored = user_service.restore_user(user_id)
    except AppError as exc:
        logger.error("Failed to restore user", exc_info=True)
        if wants_json:
            return JSONResponse({"status": "error", "message": "Không thể khôi phục người dùng"}, status_code=500)
        return HTMLResponse("Internal server error", status_code=500)

    if not restored:
        if wants_json:
            return JSONResponse({"status": "error", "message": "Tài khoản không thể khôi phục"}, status_code=404)
        return RedirectResponse("/admin/users?error=Tài khoản không thể khôi phục", status_code=303)

    if wants_json:
        try:
            restored_user = user_service.get_by_id(user_id)
        except AppError as exc:
            logger.error("Failed to fetch restored user", exc_info=True)
            return JSONResponse({"status": "error", "message": "Không thể tải dữ liệu người dùng"}, status_code=500)

        payload = None
        if restored_user:
            created_vn = _to_vietnam_time(restored_user.created_at)
            created_iso = None
            if restored_user.created_at:
                normalized = restored_user.created_at
                if normalized.tzinfo is None:
                    normalized = normalized.replace(tzinfo=timezone.utc)
                normalized = normalized.astimezone(timezone.utc)
                created_iso = normalized.isoformat(timespec="milliseconds")
            payload = {
                "id": restored_user.id,
                "email": restored_user.email,
                "role": restored_user.role,
                "created_at_iso": created_iso,
                "created_at_display": created_vn.strftime("%d/%m/%Y %H:%M") if created_vn else "-",
            }
        return JSONResponse({"status": "ok", "user": payload})

    return RedirectResponse("/admin/users?status=Đã khôi phục tài khoản", status_code=303)
