from sqlmodel import select

from app.db import get_session, init_db
from app.models import User
from app.core.jwt import hash_password
from app.services.password_reset_service import PasswordResetService

init_db()
session = get_session()
try:
    user = session.exec(select(User).where(User.email == "test@example.com")).first()
    if not user:
        user = User(email="test@example.com", hashed_password=hash_password("pass123"))
        session.add(user)
        session.commit()
        session.refresh(user)
    service = PasswordResetService(session)
    service.request_reset("test@example.com")
    print("request_reset completed")
finally:
    session.close()
