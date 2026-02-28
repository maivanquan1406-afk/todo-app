from typing import Optional, List
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import User
from app.db import get_session
from app.core.config import logger
from app.core.exceptions import DatabaseError

class UserRepository:
    def create(self, user: User) -> User:
        session = get_session()
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error("DB error in user create", exc_info=True)
            raise DatabaseError("Failed to create user", original=e) from e

    def get_by_email(self, email: str) -> Optional[User]:
        session = get_session()
        try:
            stmt = select(User).where(User.email == email)
            return session.exec(stmt).first()
        except SQLAlchemyError as e:
            logger.error("DB error in get_by_email", exc_info=True)
            raise DatabaseError("Failed to fetch user by email", original=e) from e

    def get_by_id(self, user_id: int) -> Optional[User]:
        session = get_session()
        try:
            return session.get(User, user_id)
        except SQLAlchemyError as e:
            logger.error("DB error in get_by_id", exc_info=True)
            raise DatabaseError("Failed to fetch user by id", original=e) from e

    def list_all(self) -> List[User]:
        session = get_session()
        try:
            stmt = select(User).order_by(User.created_at.desc())
            return session.exec(stmt).all()
        except SQLAlchemyError as e:
            logger.error("DB error in list_all", exc_info=True)
            raise DatabaseError("Failed to list users", original=e) from e

    def delete(self, user_id: int) -> bool:
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return False
            session.delete(user)
            session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error("DB error in delete user", exc_info=True)
            raise DatabaseError("Failed to delete user", original=e) from e
