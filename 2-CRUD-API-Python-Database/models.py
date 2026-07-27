from sqlmodel import SQLModel, Field
from typing import Optional


class Task(SQLModel, table=True):
    """Database table model representing the 'tasks' table in tasks.db."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = Field(default=False)


class TaskCreate(SQLModel):
    """Payload schema for creating a task."""

    title: str


class TaskUpdate(SQLModel):
    """Payload schema for updating a task."""

    title: Optional[str] = None
    done: Optional[bool] = None