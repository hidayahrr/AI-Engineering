from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from database import create_db_and_tables, get_db
from models import Task, TaskCreate, TaskUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when application starts up
    create_db_and_tables()
    yield


app = FastAPI(
    title="Task Management API",
    description="Interactive REST API built with FastAPI for managing tasks.",
    version="1.0.0",
    lifespan=lifespan,
)


# --- STAGE 0 ENDPOINTS ---

class Item(BaseModel):
    name: str
    description: str | None = None

db = {}

@app.post("/items/{item_id}", tags=["Stage 0"])
def create_item(item_id: int, item: Item):
    if item_id in db:
        raise HTTPException(status_code=400, detail="Item already exists")
    db[item_id] = item.dict()
    return {"message": "Item created successfully", "data": db[item_id]}

@app.get("/items/{item_id}", tags=["Stage 0"])
def read_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]

@app.put("/items/{item_id}", tags=["Stage 0"])
def update_item(item_id: int, item: Item):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id] = item.dict()
    return {"message": "Item updated successfully", "data": db[item_id]}

@app.delete("/items/{item_id}", tags=["Stage 0"])
def delete_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
    return {"message": "Item deleted successfully"}


# --- STAGE 1 ENDPOINTS ---

@app.get("/", tags=["Stage 1"], summary="Root Health & Meta")
def get_root():
    """Returns basic API metadata and available base endpoints."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", tags=["Stage 1"], summary="Health Check")
def health_check():
    """Checks whether the application server is active."""
    return {"status": "ok"}


# --- STAGE 2: IN-MEMORY DATABASE & READ ENDPOINTS ---

@app.get("/tasks", response_model=List[Task], tags=["Tasks"], summary="Get all tasks")
def get_all_tasks(db: Session = Depends(get_db)):
    """Retrieve the full list of tasks from the SQLite database."""
    tasks = db.exec(select(Task)).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=Task, tags=["Tasks"], summary="Get a task by ID")
def get_single_task(task_id: int, db: Session = Depends(get_db)):
    """Retrieve a single task by its unique ID. Returns 404 if not found."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404, 
            detail=f"Task {task_id} not found"
        )
    return task


# --- STAGE 3 ENDPOINTS ---

@app.post("/tasks", response_model=Task, status_code=201, tags=["Tasks"], summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task with an auto-incremented ID. Returns 201 Created on success."""
    if not task.title or not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required and cannot be empty"
        )
    
    new_task = Task(title=task.title.strip(), done=False)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# --- STAGE 4 ENDPOINTS ---

@app.put("/tasks/{task_id}", response_model=Task, tags=["Tasks"], summary="Update a task")
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """Update title or completion status of an existing task."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    if task_data.title is None and task_data.done is None:
        raise HTTPException(
            status_code=400,
            detail="Request body must include 'title' or 'done'"
        )
        
    if task_data.title is not None:
        if not task_data.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )
        task.title = task_data.title.strip()
        
    if task_data.done is not None:
        task.done = task_data.done
        
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Remove a task by ID. Returns HTTP 204 No Content upon successful deletion."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
        
    db.delete(task)
    db.commit()
    return Response(status_code=204)