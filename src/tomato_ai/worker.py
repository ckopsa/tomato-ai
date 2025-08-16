import time
import schedule
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from tomato_ai.domain.models import PomodoroSession
from tomato_ai.adapters.orm import PomodoroSession as ORMPomodoroSession
from tomato_ai.config import settings

def complete_expired_sessions():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        expired_sessions = (
            session.query(ORMPomodoroSession)
            .filter(ORMPomodoroSession.expires_at <= datetime.now())
            .filter(ORMPomodoroSession.state == "active")
            .all()
        )
        for orm_session in expired_sessions:
            domain_session = PomodoroSession(
                user_id=orm_session.user_id,
                session_id=orm_session.session_id,
                start_time=orm_session.start_time,
                end_time=orm_session.end_time,
                state=orm_session.state,
                duration=orm_session.duration,
                task_id=orm_session.task_id,
                expires_at=orm_session.expires_at,
                remaining_duration_on_pause=orm_session.remaining_duration_on_pause,
            )
            domain_session.complete()
            orm_session.state = domain_session.state
            orm_session.end_time = domain_session.end_time
            orm_session.expires_at = domain_session.expires_at
        session.commit()

def main():
    schedule.every(1).seconds.do(complete_expired_sessions)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
