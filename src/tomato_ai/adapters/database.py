from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from tomato_ai.config import settings
from tomato_ai.adapters.repository import SqlAlchemyRepository


def get_engine():
    return create_engine(settings.database_url)


def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        yield session


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )

    def __enter__(self):
        self.session = self.session_factory()
        self.repository = SqlAlchemyRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()