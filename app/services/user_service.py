from typing import Optional
from app.repositories.user_repository import UserRepository
from app.models import User, UserCreate, UserLogin
from app.core.jwt import hash_password, verify_password, create_access_token

repo = UserRepository()

class UserService:
    def register(self, data: UserCreate) -> User:
        existing = repo.get_by_email(data.email)
        if existing:
            return None
        hashed = hash_password(data.password)
        user = User(email=data.email, hashed_password=hashed)
        return repo.create(user)

    def login(self, data: UserLogin) -> Optional[str]:
        user = repo.get_by_email(data.email)
        if not user:
            return None
        if not verify_password(data.password, user.hashed_password):
            return None
        token = create_access_token({"sub": user.email})
        return token

    def get_by_email(self, email: str) -> Optional[User]:
        return repo.get_by_email(email)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return repo.get_by_id(user_id)

service = UserService()
