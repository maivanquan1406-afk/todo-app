from typing import Optional, List, Tuple
from datetime import datetime, date, timezone
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import Todo
from app.db import get_session
from app.core.config import logger
from app.core.exceptions import DatabaseError

class TodoRepository:
    def __init__(self):
        pass

    def create(self, todo: Todo) -> Todo:
        session = get_session()
        try:
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return todo
        except SQLAlchemyError as e:
            logger.error("DB error in create", exc_info=True)
            raise DatabaseError("Failed to create todo", original=e) from e

    def get(self, todo_id: int, owner_id: int) -> Optional[Todo]:
        session = get_session()
        try:
            stmt = select(Todo).where(
                (Todo.id == todo_id) & 
                (Todo.owner_id == owner_id) &
                (Todo.deleted_at == None)
            )
            return session.exec(stmt).first()
        except SQLAlchemyError as e:
            logger.error("DB error in get", exc_info=True)
            raise DatabaseError("Failed to fetch todo", original=e) from e

    def delete(self, todo: Todo) -> None:
        """Soft delete - set deleted_at timestamp"""
        session = get_session()
        try:
            db_todo = session.get(Todo, todo.id)
            if db_todo:
                db_todo.deleted_at = datetime.now(timezone.utc)
                session.commit()
        except SQLAlchemyError as e:
            logger.error("DB error in delete", exc_info=True)
            raise DatabaseError("Failed to delete todo", original=e) from e


    def update(self, todo: Todo) -> Todo:
        session = get_session()
        try:
            db_todo = session.get(Todo, todo.id)
            if db_todo:
                if todo.title is not None:
                    db_todo.title = todo.title
                if todo.description is not None:
                    db_todo.description = todo.description
                if todo.is_done is not None:
                    db_todo.is_done = todo.is_done
                if todo.due_date is not None:
                    db_todo.due_date = todo.due_date
                if todo.tags is not None:
                    db_todo.tags = todo.tags
                db_todo.updated_at = todo.updated_at
                session.commit()
                session.refresh(db_todo)
                return db_todo
            return None
        except SQLAlchemyError as e:
            logger.error("DB error in update", exc_info=True)
            raise DatabaseError("Failed to update todo", original=e) from e

    def list(
        self,
        owner_id: int,
        *,
        limit: int = 10,
        offset: int = 0,
        q: Optional[str] = None,
        is_done: Optional[bool] = None,
        sort: Optional[str] = None
    ) -> Tuple[List[Todo], int]:
        session = get_session()
        try:
            base_filter = (Todo.owner_id == owner_id) & (Todo.deleted_at == None)
            stmt = select(Todo).where(base_filter)
            count_stmt = select(Todo).where(base_filter)

            if q:
                stmt = stmt.where(Todo.title.contains(q))
                count_stmt = count_stmt.where(Todo.title.contains(q))
            if is_done is not None:
                stmt = stmt.where(Todo.is_done == is_done)
                count_stmt = count_stmt.where(Todo.is_done == is_done)
            if sort:
                if sort.startswith("-"):
                    key = sort[1:]
                    if key == "created_at":
                        stmt = stmt.order_by(Todo.created_at.desc())
                else:
                    if sort == "created_at":
                        stmt = stmt.order_by(Todo.created_at)

            stmt = stmt.offset(offset).limit(limit)
            items = session.exec(stmt).all()
            total = len(session.exec(count_stmt).all())
            return items, total
        except SQLAlchemyError as e:
            logger.error("DB error in list", exc_info=True)
            raise DatabaseError("Failed to list todos", original=e) from e
    def get_overdue(self, owner_id: int) -> List[Todo]:
        """Get incomplete (non-deleted) todo items with due_date in the past"""
        session = get_session()
        now = datetime.now(timezone.utc)
        try:
            stmt = select(Todo).where(
                (Todo.owner_id == owner_id) &
                (Todo.due_date < now) &
                (Todo.is_done == False) &
                (Todo.deleted_at == None)
            )
            return session.exec(stmt).all()
        except SQLAlchemyError as e:
            logger.error("DB error in get_overdue", exc_info=True)
            raise DatabaseError("Failed to fetch overdue todos", original=e) from e

    def get_today(self, owner_id: int) -> List[Todo]:
        """Get incomplete (non-deleted) todo items with due_date today"""
        session = get_session()
        today = datetime.now(timezone.utc)
        today_start = datetime.combine(today.date(), datetime.min.time(), tzinfo=timezone.utc)
        today_end = datetime.combine(today.date(), datetime.max.time(), tzinfo=timezone.utc)
        try:
            stmt = select(Todo).where(
                (Todo.owner_id == owner_id) &
                (Todo.due_date >= today_start) &
                (Todo.due_date <= today_end) &
                (Todo.is_done == False) &
                (Todo.deleted_at == None)
            )
            return session.exec(stmt).all()
        except SQLAlchemyError as e:
            logger.error("DB error in get_today", exc_info=True)
            raise DatabaseError("Failed to fetch today's todos", original=e) from e