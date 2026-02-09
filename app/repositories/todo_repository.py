from typing import Optional, List, Tuple
from datetime import datetime, date
from sqlmodel import select
from app.models import Todo
from app.db import get_session

class TodoRepository:
    def __init__(self):
        pass

    def create(self, todo: Todo) -> Todo:
        session = get_session()
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo

    def get(self, todo_id: int, owner_id: int) -> Optional[Todo]:
        session = get_session()
        stmt = select(Todo).where(
            (Todo.id == todo_id) & 
            (Todo.owner_id == owner_id) &
            (Todo.deleted_at == None)
        )
        return session.exec(stmt).first()

    def delete(self, todo: Todo) -> None:
        """Soft delete - set deleted_at timestamp"""
        session = get_session()
        db_todo = session.get(Todo, todo.id)
        if db_todo:
            db_todo.deleted_at = datetime.utcnow()
            session.commit()


    def update(self, todo: Todo) -> Todo:
        session = get_session()
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

    def list(self, owner_id: int, *, limit: int = 10, offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None) -> Tuple[List[Todo], int]:
        session = get_session()
        # Only include non-deleted todos
        stmt = select(Todo).where(
            (Todo.owner_id == owner_id) &
            (Todo.deleted_at == None)
        )
        if q:
            stmt = stmt.where(Todo.title.contains(q))
        if is_done is not None:
            stmt = stmt.where(Todo.is_done == is_done)
        if sort:
            if sort.startswith("-"):
                key = sort[1:]
                if key == "created_at":
                    stmt = stmt.order_by(Todo.created_at.desc())
            else:
                if sort == "created_at":
                    stmt = stmt.order_by(Todo.created_at)
        
        count_stmt = select(Todo).where(
            (Todo.owner_id == owner_id) &
            (Todo.deleted_at == None)
        )
        if q:
            count_stmt = count_stmt.where(Todo.title.contains(q))
        if is_done is not None:
            count_stmt = count_stmt.where(Todo.is_done == is_done)
        
        all_todos = session.exec(count_stmt).all()
        count = len(all_todos)
        
        stmt = stmt.offset(offset).limit(limit)
        results = session.exec(stmt).all()
        return results, count
    def get_overdue(self, owner_id: int) -> List[Todo]:
        """Get incomplete (non-deleted) todo items with due_date in the past"""
        session = get_session()
        now = datetime.utcnow()
        stmt = select(Todo).where(
            (Todo.owner_id == owner_id) &
            (Todo.due_date < now) &
            (Todo.is_done == False) &
            (Todo.deleted_at == None)
        )
        return session.exec(stmt).all()

    def get_today(self, owner_id: int) -> List[Todo]:
        """Get incomplete (non-deleted) todo items with due_date today"""
        session = get_session()
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        stmt = select(Todo).where(
            (Todo.owner_id == owner_id) &
            (Todo.due_date >= today_start) &
            (Todo.due_date <= today_end) &
            (Todo.is_done == False) &
            (Todo.deleted_at == None)
        )
        return session.exec(stmt).all()