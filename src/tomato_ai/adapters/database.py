import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tomato_ai.config import settings

def get_engine():
    if os.environ.get("TESTING"):
        return create_engine(
            "sqlite:///file:memdb1?mode=memory&cache=shared&uri=true",
            connect_args={"check_same_thread": False},
        )
    return create_engine(settings.database_url)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()