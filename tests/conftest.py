import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tomato_ai.entrypoints.fastapi_app import create_app
from tomato_ai.adapters.database import get_session
from tomato_ai.adapters.orm import Base
from tomato_ai.config import settings


@pytest.fixture()
def client():
    with patch.object(settings, 'TELEGRAM_BOT_TOKEN', 'dummy-token'), \
         patch.dict('os.environ', {'TESTING': 'True'}):

        test_engine = create_engine(
            "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=test_engine)

        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        def override_get_session():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app = create_app()
        app.dependency_overrides[get_session] = override_get_session

        with TestClient(app) as c:
            yield c

        Base.metadata.drop_all(bind=test_engine)
        app.dependency_overrides.clear()
