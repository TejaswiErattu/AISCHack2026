"""Shared test fixtures for API endpoint tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.database import Base, get_db
from backend.main import app
from backend.seed import seed_database


@pytest.fixture
def seeded_client():
    """TestClient with an in-memory SQLite DB, tables created and seeded.

    Uses StaticPool so all connections share the same in-memory DB
    (default :memory: creates a new empty DB per connection).
    Overrides the get_db dependency so all endpoints use the test DB.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    # Seed the test DB
    db = TestSession()
    seed_database(db)
    db.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
