import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from tomato_ai.entrypoints.fastapi_app import create_app
from tomato_ai.adapters.orm import Base
from tomato_ai.config import settings
from tomato_ai.adapters.database import get_engine

os.environ["TESTING"] = "True"


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with patch.object(settings, 'TELEGRAM_BOT_TOKEN', 'dummy-token'), \
         patch("apscheduler.schedulers.asyncio.AsyncIOScheduler.start"), \
         patch("apscheduler.schedulers.asyncio.AsyncIOScheduler.shutdown"):
        app = create_app()
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def scheduler_client():
    with patch.object(settings, 'TELEGRAM_BOT_TOKEN', 'dummy-token'):
        app = create_app()
        with TestClient(app) as c:
            yield c
