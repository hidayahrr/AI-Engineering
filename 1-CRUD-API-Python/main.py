from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

app = FastAPI(
    title="Task Management API",
    description="Interactive REST API built with FastAPI for managing tasks.",
    version="1.0.0"
)

# Task Request Schemas
class TaskCreate(BaseModel):
    title: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

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

tasks_db = [
    {"id": 1, "title": "Setup repository", "done": True},
    {"id": 2, "title": "Build Stage 1 endpoints", "done": True},
    {"id": 3, "title": "Implement Stage 2 endpoints", "done": False}
]

@app.get("/tasks", tags=["Tasks"], summary="Get all tasks")
def get_all_tasks():
    """Retrieve the full list of tasks from the in-memory database."""
    return tasks_db

@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get a task by ID")
def get_single_task(task_id: int):
    """Retrieve a single task by its unique ID. Returns 404 if not found."""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=404, 
        detail=f"Task {task_id} not found"
    )

# --- STAGE 3 ENDPOINTS ---

@app.post("/tasks", status_code=201, tags=["Tasks"], summary="Create a new task")
def create_task(task: TaskCreate):
    """Create a new task with an auto-incremented ID. Returns 201 Created on success."""
    if not task.title or not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required and cannot be empty"
        )
    
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": new_id,
        "title": task.title.strip(),
        "done": False
    }
    
    tasks_db.append(new_task)
    return new_task

# --- STAGE 4 ENDPOINTS ---

@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Update a task")
def update_task(task_id: int, task_data: TaskUpdate):
    """Update title or completion status of an existing task."""
    target_task = None
    for task in tasks_db:
        if task["id"] == task_id:
            target_task = task
            break
            
    if not target_task:
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
        target_task["title"] = task_data.title.strip()
        
    if task_data.done is not None:
        target_task["done"] = task_data.done
        
    return target_task

@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    """Remove a task by ID. Returns HTTP 204 No Content upon successful deletion."""
    global tasks_db
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(i)
            return Response(status_code=204)
            
    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )