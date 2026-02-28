from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(bind=engine)
    _ensure_user_role_column()


def _ensure_user_role_column():
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("user")}
    if "role" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'user\''))
        conn.execute(text('UPDATE "user" SET role = \'user\' WHERE role IS NULL'))

def get_session():
    return Session(engine)
