from typing import Callable, Optional

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import inspect, text

from app.core.config import settings, logger
from app.core.jwt import hash_password, verify_password
from app.models import User

engine = create_engine(settings.DATABASE_URL, echo=False)
_session_override: Optional[Callable[[], Session]] = None

def init_db():
    SQLModel.metadata.create_all(bind=engine)
    _ensure_user_columns()
    _ensure_todo_columns()
    _ensure_default_admin()

def _ensure_user_columns():
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("user")}
    statements: list[str] = []
    if "role" not in columns:
        statements.append('ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'user\'')
        statements.append('UPDATE "user" SET role = \'user\' WHERE role IS NULL')
    if "otp_code" not in columns:
        statements.append('ALTER TABLE "user" ADD COLUMN otp_code VARCHAR(6)')
    if "otp_expire" not in columns:
        statements.append('ALTER TABLE "user" ADD COLUMN otp_expire DATETIME')
    if "otp_used" not in columns:
        statements.append('ALTER TABLE "user" ADD COLUMN otp_used BOOLEAN DEFAULT 0')
        statements.append('UPDATE "user" SET otp_used = 0 WHERE otp_used IS NULL')
    if "deleted_at" not in columns:
        statements.append('ALTER TABLE "user" ADD COLUMN deleted_at DATETIME')
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def _ensure_todo_columns():
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    if "todo" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("todo")}
    statements: list[str] = []
    if "reminder_sent_at" not in columns:
        statements.append('ALTER TABLE "todo" ADD COLUMN reminder_sent_at DATETIME')
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def _ensure_default_admin():
    email = settings.DEFAULT_ADMIN_EMAIL
    password = settings.DEFAULT_ADMIN_PASSWORD
    if not email or not password:
        return
    session = Session(engine)
    try:
        user = session.exec(select(User).where(User.email == email)).first()
        hashed = hash_password(password)
        if not user:
            user = User(email=email, hashed_password=hashed, role="admin")
            session.add(user)
            session.commit()
            logger.info("Created default admin user %s", email)
            return
        updated = False
        if user.role != "admin":
            user.role = "admin"
            updated = True
        if not verify_password(password, user.hashed_password):
            user.hashed_password = hashed
            updated = True
        if updated:
            session.commit()
            logger.info("Updated default admin user %s", email)
    except Exception:
        session.rollback()
        logger.warning("Failed to ensure default admin user", exc_info=True)
    finally:
        session.close()

def get_session():
    if _session_override is not None:
        return _session_override()
    return Session(engine)


def set_session_override(factory: Callable[[], Session] | None) -> None:
    """Allow tests to inject a custom session factory."""
    global _session_override
    _session_override = factory
