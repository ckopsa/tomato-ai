
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tomato_ai.entrypoints.fastapi_app import create_app
from tomato_ai.adapters.database import get_session
from tomato_ai.adapters.orm import Base
from tomato_ai.config import settings


@pytest.fixture(autouse=True)
def override_settings(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(settings, "TEST_DATABASE_URL", f"sqlite:///{db_path}")


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_db():
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_db
    with TestClient(app) as client:
        yield client
