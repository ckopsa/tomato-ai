import os
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="function")
def session():
    # Create a temporary file for the SQLite database
    db_fd, db_path = tempfile.mkstemp()
    TEST_DB_URL = f"sqlite:///{db_path}"

    # Set up the test database
    os.environ["TEST_DATABASE_URL"] = TEST_DB_URL
    engine = create_engine(TEST_DB_URL)

    # Run alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(alembic_cfg, "head")

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    # The test runs here
    yield db

    # Tear down the test database
    db.close()
    os.close(db_fd)
    os.unlink(db_path)
    del os.environ["TEST_DATABASE_URL"]
