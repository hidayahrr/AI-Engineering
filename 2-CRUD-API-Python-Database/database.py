from sqlmodel import SQLModel, create_engine, Session, select
from typing import Generator

# SQLite database file named tasks.db
sqlite_file_name = "tasks.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Create the tasks table if it doesn't exist, and seed 3 initial tasks if empty."""
    # 1. Create table if it doesn't exist
    SQLModel.metadata.create_all(engine)

    # 2. Check if the table is empty and seed data
    with Session(engine) as session:
        # Import Task locally inside function to avoid circular import issues
        from models import Task

        existing_tasks = session.exec(select(Task)).all()

        if not existing_tasks:
            example_tasks = [
                Task(title="Setup repository", done=True),
                Task(title="Build Stage 1 endpoints", done=True),
                Task(title="Implement Stage 2 endpoints", done=False),
            ]
            session.add_all(example_tasks)
            session.commit()


def get_db() -> Generator[Session, None, None]:
    """Provide a database session per HTTP request."""
    with Session(engine) as session:
        yield session