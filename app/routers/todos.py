from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import math

from app.services.todo_service import service
from app.models import TodoCreate, TodoUpdate, Todo
from app.routers.auth import get_current_user
from app.core.exceptions import AppError, ValidationError, ConflictError, NotFoundError, DatabaseError

router = APIRouter()


def _map_app_error(exc: AppError) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DatabaseError):
        return HTTPException(status_code=500, detail="internal server error")
    return HTTPException(status_code=500, detail="internal server error")

@router.get("/overdue", tags=["todos"])
def get_overdue(current_user = Depends(get_current_user)):
    try:
        todos = service.get_overdue(current_user.id)
        return {"items": todos, "total": len(todos)}
    except AppError as exc:
        raise _map_app_error(exc)

@router.get("/today", tags=["todos"])
def get_today(current_user = Depends(get_current_user)):
    try:
        todos = service.get_today(current_user.id)
        return {"items": todos, "total": len(todos)}
    except AppError as exc:
        raise _map_app_error(exc)

@router.get("/", tags=["todos"])
def list_todos(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    q: Optional[str] = None,
    is_done: Optional[bool] = None,
    sort: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    try:
        effective_limit = page_size or limit
        effective_page = page or (offset // effective_limit + 1)
        effective_offset = (effective_page - 1) * effective_limit
        items, total = service.list(
            current_user.id,
            limit=effective_limit,
            offset=effective_offset,
            q=q,
            is_done=is_done,
            sort=sort
        )
        total_pages = math.ceil(total / effective_limit) if effective_limit else 1
        return {
            "items": items,
            "total": total,
            "limit": effective_limit,
            "offset": effective_offset,
            "page": effective_page,
            "page_size": effective_limit,
            "total_pages": total_pages
        }
    except AppError as exc:
        raise _map_app_error(exc)

@router.post("/", response_model=Todo)
def create_todo(payload: TodoCreate, current_user = Depends(get_current_user)):
    try:
        if not (3 <= len(payload.title) <= 100):
            raise ValidationError("title length must be 3-100", field="title")
        todo = service.create(payload, current_user.id)
        return todo
    except AppError as exc:
        raise _map_app_error(exc)

@router.get("/{todo_id}")
def get_todo(todo_id: int, current_user = Depends(get_current_user)):
    try:
        return service.get(todo_id, current_user.id)
    except AppError as exc:
        raise _map_app_error(exc)

@router.put("/{todo_id}")
def put_todo(todo_id: int, payload: TodoCreate, current_user = Depends(get_current_user)):
    try:
        if not (3 <= len(payload.title) <= 100):
            raise ValidationError("title length must be 3-100", field="title")
        updated = service.update(
            todo_id,
            current_user.id,
            TodoUpdate(
                title=payload.title,
                description=payload.description,
                due_date=payload.due_date,
                tags=payload.tags
            )
        )
        return updated
    except AppError as exc:
        raise _map_app_error(exc)

@router.patch("/{todo_id}")
def patch_todo(todo_id: int, payload: TodoUpdate, current_user = Depends(get_current_user)):
    try:
        if payload.title is not None and not (3 <= len(payload.title) <= 100):
            raise ValidationError("title length must be 3-100", field="title")
        updated = service.update(todo_id, current_user.id, payload)
        return updated
    except AppError as exc:
        raise _map_app_error(exc)

@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, current_user = Depends(get_current_user)):
    try:
        service.delete(todo_id, current_user.id)
    except AppError as exc:
        raise _map_app_error(exc)

@router.post("/{todo_id}/complete")
def complete_todo(todo_id: int, current_user = Depends(get_current_user)):
    try:
        return service.mark_complete(todo_id, current_user.id)
    except AppError as exc:
        raise _map_app_error(exc)

