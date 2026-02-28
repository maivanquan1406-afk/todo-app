from typing import Optional, Tuple
from datetime import datetime, timezone

from app.repositories.todo_repository import TodoRepository
from app.models import Todo, TodoCreate, TodoUpdate
from app.core.config import logger
from app.core.exceptions import DatabaseError, NotFoundError

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
        try:
            return repo.create(todo)
        except DatabaseError as e:
            logger.error("Service error in create", exc_info=True)
            raise e

    def get(self, todo_id: int, owner_id: int) -> Todo:
        try:
            todo = repo.get(todo_id, owner_id)
        except DatabaseError as e:
            logger.error("Service error in get", exc_info=True)
            raise e
        if not todo:
            raise NotFoundError("todo")
        return todo

    def delete(self, todo_id: int, owner_id: int) -> bool:
        try:
            todo = repo.get(todo_id, owner_id)
            if not todo:
                raise NotFoundError("todo")
            repo.delete(todo)
            return True
        except DatabaseError as e:
            logger.error("Service error in delete", exc_info=True)
            raise e

    def update(self, todo_id: int, owner_id: int, data: TodoUpdate) -> Todo:
        try:
            todo = repo.get(todo_id, owner_id)
            if not todo:
                raise NotFoundError("todo")
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
            todo.updated_at = datetime.now(timezone.utc)
            updated = repo.update(todo)
            if not updated:
                raise NotFoundError("todo")
            return updated
        except DatabaseError as e:
            logger.error("Service error in update", exc_info=True)
            raise e

    def list(self, owner_id: int, limit: int = 10, offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None) -> Tuple[list, int]:
        try:
            return repo.list(owner_id, limit=limit, offset=offset, q=q, is_done=is_done, sort=sort)
        except DatabaseError as e:
            logger.error("Service error in list", exc_info=True)
            raise e

    def mark_complete(self, todo_id: int, owner_id: int) -> Todo:
        try:
            todo = repo.get(todo_id, owner_id)
            if not todo:
                raise NotFoundError("todo")
            todo.is_done = True
            todo.updated_at = datetime.now(timezone.utc)
            updated = repo.update(todo)
            if not updated:
                raise NotFoundError("todo")
            return updated
        except DatabaseError as e:
            logger.error("Service error in mark_complete", exc_info=True)
            raise e

    def get_overdue(self, owner_id: int):
        try:
            return repo.get_overdue(owner_id)
        except DatabaseError as e:
            logger.error("Service error in get_overdue", exc_info=True)
            raise e

    def get_today(self, owner_id: int):
        try:
            return repo.get_today(owner_id)
        except DatabaseError as e:
            logger.error("Service error in get_today", exc_info=True)
            raise e

service = TodoService()

