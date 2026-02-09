from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class TodoBase(SQLModel):
    title: str
    description: Optional[str] = None
    is_done: bool = False

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TodoCreate(SQLModel):
    title: str
    description: Optional[str] = None

class TodoUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_done: Optional[bool] = None
