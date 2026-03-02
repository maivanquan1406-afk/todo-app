import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.db import get_session, set_session_override


@pytest.fixture(scope="function")
def session():
    """Create a new in-memory database session for each test"""
    # Create in-memory SQLite database - completely isolated per test
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    # Create all tables fresh for each test
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session_instance:
        set_session_override(lambda: session_instance)
        yield session_instance

    # Clean up after test
    set_session_override(None)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(session: Session):
    """Create a test client with database override"""
    # Override the database session dependency
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    
    # Create client
    client = TestClient(app)
    
    yield client
    
    # Clear overrides after test
    app.dependency_overrides.clear()



