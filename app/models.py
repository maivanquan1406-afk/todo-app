from typing import Optional
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    role: str = Field(default="user", max_length=20)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=_utcnow)

class UserCreate(SQLModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=100)

class UserLogin(SQLModel):
    email: EmailStr
    password: str = Field(min_length=5, max_length=100)

class UserResponse(UserBase):
    id: int
    created_at: datetime

class TodoBase(SQLModel):
    title: str
    description: Optional[str] = None
    is_done: bool = False
    due_date: Optional[datetime] = None
    tags: Optional[str] = None

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    deleted_at: Optional[datetime] = None

class TodoCreate(SQLModel):
    title: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    due_date: Optional[datetime] = None
    tags: Optional[str] = Field(default=None, max_length=255)

class TodoUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_done: Optional[bool] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = Field(default=None, max_length=255)

class TodoResponse(TodoBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    email: Optional[str] = None

