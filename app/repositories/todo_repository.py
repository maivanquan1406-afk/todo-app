from typing import Optional, List, Tuple
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

    def get(self, todo_id: int) -> Optional[Todo]:
        session = get_session()
        result = session.get(Todo, todo_id)
        return result

    def delete(self, todo: Todo) -> None:
        session = get_session()
        # Refetch from DB to avoid session attachment issues
        db_todo = session.get(Todo, todo.id)
        if db_todo:
            session.delete(db_todo)
            session.commit()

    def update(self, todo: Todo) -> Todo:
        session = get_session()
        # Refetch from DB to avoid session attachment issues
        db_todo = session.get(Todo, todo.id)
        if db_todo:
            if todo.title is not None:
                db_todo.title = todo.title
            if todo.description is not None:
                db_todo.description = todo.description
            if todo.is_done is not None:
                db_todo.is_done = todo.is_done
            db_todo.updated_at = todo.updated_at
            session.commit()
            session.refresh(db_todo)
            return db_todo
        return None

    def list(self, *, limit: int = 10, offset: int = 0, q: Optional[str] = None, is_done: Optional[bool] = None, sort: Optional[str] = None) -> Tuple[List[Todo], int]:
        session = get_session()
        stmt = select(Todo)
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
        
        count_stmt = select(Todo)
        if q:
            count_stmt = count_stmt.where(Todo.title.contains(q))
        if is_done is not None:
            count_stmt = count_stmt.where(Todo.is_done == is_done)
        
        all_todos = session.exec(count_stmt).all()
        count = len(all_todos)
        
        stmt = stmt.offset(offset).limit(limit)
        results = session.exec(stmt).all()
        return results, count
