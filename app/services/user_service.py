from typing import Optional, List

from app.repositories.user_repository import UserRepository
from app.models import User, UserCreate, UserLogin
from app.core.jwt import hash_password, verify_password, create_access_token
from app.core.config import logger
from app.core.exceptions import DatabaseError, ConflictError, ValidationError, AuthenticationError

repo = UserRepository()

class UserService:
    def register(self, data: UserCreate) -> User:
        try:
            existing = repo.get_by_email(data.email)
            if existing:
                raise ConflictError("email already exists")
            hashed = hash_password(data.password)
            user = User(email=data.email, hashed_password=hashed, role="user")
            return repo.create(user)
        except DatabaseError as e:
            logger.error("Service error in register", exc_info=True)
            raise e

    def login(self, data: UserLogin) -> str:
        try:
            user = repo.get_by_email(data.email)
            if not user or not verify_password(data.password, user.hashed_password):
                raise AuthenticationError("invalid email or password")
            token = create_access_token({"sub": user.email})
            return token
        except DatabaseError as e:
            logger.error("Service error in login", exc_info=True)
            raise e

    def get_by_email(self, email: str) -> Optional[User]:
        try:
            return repo.get_by_email(email)
        except DatabaseError as e:
            logger.error("Service error in get_by_email", exc_info=True)
            raise e

    def get_by_id(self, user_id: int) -> Optional[User]:
        try:
            return repo.get_by_id(user_id)
        except DatabaseError as e:
            logger.error("Service error in get_by_id", exc_info=True)
            raise e

    def list_all(self) -> List[User]:
        try:
            return repo.list_all()
        except DatabaseError as e:
            logger.error("Service error in list_all", exc_info=True)
            raise e

    def delete_user(self, user_id: int) -> bool:
        try:
            return repo.delete(user_id)
        except DatabaseError as e:
            logger.error("Service error in delete_user", exc_info=True)
            raise e

service = UserService()
