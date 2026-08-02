import os
import redis
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session, select

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app_user:app_password@db:5432/task_db")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

engine = create_engine(DATABASE_URL, echo=False)

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def create_db_and_tables() -> None:
    """Create tables if they don't exist and seed default tasks."""
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        from models import Task
        existing = session.exec(select(Task)).first()
        if not existing:
            example_tasks = [
                Task(title="Setup repository", done=True),
                Task(title="Build Stage 1 endpoints", done=True),
                Task(title="Implement Stage 2 endpoints", done=False),
            ]
            session.add_all(example_tasks)
            session.commit()

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def check_redis_ping() -> bool:
    """Stretch goal: Ping Redis server."""
    try:
        return redis_client.ping()
    except Exception:
        return False