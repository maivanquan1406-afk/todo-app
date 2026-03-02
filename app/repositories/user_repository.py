from datetime import datetime, timezone
from typing import Optional, List, Iterable
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from app.models import User
from app.db import get_session
from app.core.config import logger
from app.core.exceptions import DatabaseError

class UserRepository:
    def create(self, user: User) -> User:
        with get_session() as session:
            try:
                session.add(user)
                session.commit()
                session.refresh(user)
                return user
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB error in user create", exc_info=True)
                raise DatabaseError("Failed to create user", original=e) from e

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> Optional[User]:
        with get_session() as session:
            try:
                stmt = select(User).where(User.email == email)
                if not include_deleted:
                    stmt = stmt.where(User.deleted_at.is_(None))
                return session.exec(stmt).first()
            except SQLAlchemyError as e:
                logger.error("DB error in get_by_email", exc_info=True)
                raise DatabaseError("Failed to fetch user by email", original=e) from e

    def get_by_id(self, user_id: int, *, include_deleted: bool = False) -> Optional[User]:
        with get_session() as session:
            try:
                user = session.get(User, user_id)
                if user and not include_deleted and user.deleted_at is not None:
                    return None
                return user
            except SQLAlchemyError as e:
                logger.error("DB error in get_by_id", exc_info=True)
                raise DatabaseError("Failed to fetch user by id", original=e) from e

    def list_all(
        self,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[User]:
        with get_session() as session:
            try:
                stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
                if search:
                    pattern = f"%{search.lower()}%"
                    stmt = stmt.where(func.lower(User.email).like(pattern))
                if start_date:
                    stmt = stmt.where(User.created_at >= start_date)
                if end_date:
                    stmt = stmt.where(User.created_at <= end_date)
                return session.exec(stmt).all()
            except SQLAlchemyError as e:
                logger.error("DB error in list_all", exc_info=True)
                raise DatabaseError("Failed to list users", original=e) from e

    def list_deleted(
        self,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[User]:
        with get_session() as session:
            try:
                stmt = select(User).where(User.deleted_at.is_not(None)).order_by(User.deleted_at.desc())
                if search:
                    pattern = f"%{search.lower()}%"
                    stmt = stmt.where(func.lower(User.email).like(pattern))
                if start_date:
                    stmt = stmt.where(User.created_at >= start_date)
                if end_date:
                    stmt = stmt.where(User.created_at <= end_date)
                return session.exec(stmt).all()
            except SQLAlchemyError as e:
                logger.error("DB error in list_deleted", exc_info=True)
                raise DatabaseError("Failed to list deleted users", original=e) from e

    def delete(self, user_id: int) -> bool:
        with get_session() as session:
            try:
                user = session.get(User, user_id)
                if not user or user.deleted_at is not None:
                    return False
                user.deleted_at = datetime.now(timezone.utc)
                user.is_active = False
                session.add(user)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB error in delete user", exc_info=True)
                raise DatabaseError("Failed to delete user", original=e) from e

    def restore(self, user_id: int) -> bool:
        with get_session() as session:
            try:
                user = session.get(User, user_id)
                if not user or user.deleted_at is None:
                    return False
                user.deleted_at = None
                user.is_active = True
                session.add(user)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB error in restore user", exc_info=True)
                raise DatabaseError("Failed to restore user", original=e) from e

    def reactivate_deleted_user(self, user: User, hashed_password: str) -> User:
        with get_session() as session:
            try:
                db_user = session.get(User, user.id)
                if not db_user or db_user.deleted_at is None:
                    raise DatabaseError("User is not marked as deleted")
                db_user.hashed_password = hashed_password
                db_user.deleted_at = None
                db_user.is_active = True
                db_user.created_at = datetime.now(timezone.utc)
                db_user.otp_code = None
                db_user.otp_expire = None
                db_user.otp_used = False
                session.add(db_user)
                session.commit()
                session.refresh(db_user)
                return db_user
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB error in reactivate_deleted_user", exc_info=True)
                raise DatabaseError("Failed to reactivate deleted user", original=e) from e

    def delete_by_date_range(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        exclude_ids: Optional[Iterable[int]] = None,
    ) -> int:
        with get_session() as session:
            exclude_ids = set(exclude_ids or [])
            try:
                stmt = select(User).where(User.deleted_at.is_(None))
                if start_date:
                    stmt = stmt.where(User.created_at >= start_date)
                if end_date:
                    stmt = stmt.where(User.created_at <= end_date)
                users = session.exec(stmt).all()
                deleted = 0
                for user in users:
                    if exclude_ids and user.id in exclude_ids:
                        continue
                    user.deleted_at = datetime.now(timezone.utc)
                    user.is_active = False
                    session.add(user)
                    deleted += 1
                if deleted:
                    session.commit()
                else:
                    session.rollback()
                return deleted
            except SQLAlchemyError as e:
                session.rollback()
                logger.error("DB error in delete_by_date_range", exc_info=True)
                raise DatabaseError("Failed to delete users by date", original=e) from e
