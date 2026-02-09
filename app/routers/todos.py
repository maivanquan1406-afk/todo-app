from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.todo_service import service
from app.models import TodoCreate, TodoUpdate, Todo

router = APIRouter()

@router.get("/", tags=["todos"])
def list_todos(limit: int = Query(10, ge=1, le=100), offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None):
    items, total = service.list(limit=limit, offset=offset, q=q, is_done=is_done, sort=sort)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.post("/", response_model=Todo)
def create_todo(payload: TodoCreate):
    if not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    todo = service.create(payload)
    return todo

@router.get("/{todo_id}")
def get_todo(todo_id: int):
    todo = service.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Not found")
    return todo

@router.put("/{todo_id}")
def put_todo(todo_id: int, payload: TodoCreate):
    if not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    updated = service.update(todo_id, TodoUpdate(title=payload.title, description=payload.description))
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

@router.patch("/{todo_id}")
def patch_todo(todo_id: int, payload: TodoUpdate):
    if payload.title is not None and not (3 <= len(payload.title) <= 100):
        raise HTTPException(status_code=422, detail="title length must be 3-100")
    updated = service.update(todo_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated

@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    ok = service.delete(todo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")

@router.post("/{todo_id}/complete")
def complete_todo(todo_id: int):
    updated = service.mark_complete(todo_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return updated
