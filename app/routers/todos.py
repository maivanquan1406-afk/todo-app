from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.services.todo_service import service
from app.models import TodoCreate, TodoUpdate, Todo
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/overdue", tags=["todos"])
def get_overdue(current_user = Depends(get_current_user)):
    todos = service.get_overdue(current_user.id)
    return {"items": todos, "total": len(todos)}

@router.get("/today", tags=["todos"])
def get_today(current_user = Depends(get_current_user)):
    todos = service.get_today(current_user.id)
    return {"items": todos, "total": len(todos)}

@router.get("/", tags=["todos"])
def list_todos(limit: int = Query(10, ge=1, le=100), offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None, current_user = Depends(get_current_user)):
    items, total = service.list(current_user.id, limit=limit, offset=offset, q=q, is_done=is_done, sort=sort)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.post("/", response_model=Todo)
def create_todo(payload: TodoCreate, current_user = Depends(get_current_user)):
    if not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    todo = service.create(payload, current_user.id)
    return todo

@router.get("/{todo_id}")
def get_todo(todo_id: int, current_user = Depends(get_current_user)):
    todo = service.get(todo_id, current_user.id)
    if not todo:
        raise HTTPException(status_code=404, detail="Not found")
    return todo

@router.put("/{todo_id}")
def put_todo(todo_id: int, payload: TodoCreate, current_user = Depends(get_current_user)):
    if not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    updated = service.update(todo_id, current_user.id, TodoUpdate(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        tags=payload.tags
    ))
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

@router.patch("/{todo_id}")
def patch_todo(todo_id: int, payload: TodoUpdate, current_user = Depends(get_current_user)):
    if payload.title is not None and not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    updated = service.update(todo_id, current_user.id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, current_user = Depends(get_current_user)):
    ok = service.delete(todo_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")

@router.post("/{todo_id}/complete")
def complete_todo(todo_id: int, current_user = Depends(get_current_user)):
    updated = service.mark_complete(todo_id, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

