from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tomato_ai.config import settings

def get_engine():
    return create_engine(settings.database_url)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        yield session