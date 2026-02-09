from typing import Optional, Tuple
from datetime import datetime
from app.repositories.todo_repository import TodoRepository
from app.models import Todo, TodoCreate, TodoUpdate

repo = TodoRepository()

class TodoService:
    def create(self, data: TodoCreate, owner_id: int) -> Todo:
        todo = Todo(
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            tags=data.tags,
            owner_id=owner_id
        )
        return repo.create(todo)

    def get(self, todo_id: int, owner_id: int) -> Optional[Todo]:
        return repo.get(todo_id, owner_id)

    def delete(self, todo_id: int, owner_id: int) -> bool:
        todo = repo.get(todo_id, owner_id)
        if not todo:
            return False
        repo.delete(todo)
        return True

    def update(self, todo_id: int, owner_id: int, data: TodoUpdate) -> Optional[Todo]:
        todo = repo.get(todo_id, owner_id)
        if not todo:
            return None
        if data.title is not None:
            todo.title = data.title
        if data.description is not None:
            todo.description = data.description
        if data.is_done is not None:
            todo.is_done = data.is_done
        if data.due_date is not None:
            todo.due_date = data.due_date
        if data.tags is not None:
            todo.tags = data.tags
        todo.updated_at = datetime.utcnow()
        return repo.update(todo)

    def list(self, owner_id: int, limit: int = 10, offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None) -> Tuple[list, int]:
        return repo.list(owner_id, limit=limit, offset=offset, q=q, is_done=is_done, sort=sort)

    def mark_complete(self, todo_id: int, owner_id: int):
        todo = repo.get(todo_id, owner_id)
        if not todo:
            return None
        todo.is_done = True
        todo.updated_at = datetime.utcnow()
        return repo.update(todo)

    def get_overdue(self, owner_id: int):
        return repo.get_overdue(owner_id)

    def get_today(self, owner_id: int):
        return repo.get_today(owner_id)

service = TodoService()

