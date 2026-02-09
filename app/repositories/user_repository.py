from typing import Optional
from sqlmodel import select
from app.models import User
from app.db import get_session
from app.core.jwt import hash_password, verify_password

class UserRepository:
    def create(self, user: User) -> User:
        session = get_session()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        session = get_session()
        stmt = select(User).where(User.email == email)
        return session.exec(stmt).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        session = get_session()
        return session.get(User, user_id)
