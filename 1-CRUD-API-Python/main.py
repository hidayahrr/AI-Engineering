from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Task Request Schema for Creation
class TaskCreate(BaseModel):
    title: str | None = None

# --- STAGE 0 ENDPOINTS ---

class Item(BaseModel):
    name: str
    description: str | None = None

db = {}

@app.post("/items/{item_id}")
def create_item(item_id: int, item: Item):
    if item_id in db:
        raise HTTPException(status_code=400, detail="Item already exists")
    db[item_id] = item.dict()
    return {"message": "Item created successfully", "data": db[item_id]}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id] = item.dict()
    return {"message": "Item updated successfully", "data": db[item_id]}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
    return {"message": "Item deleted successfully"}

# --- STAGE 1 ENDPOINTS ---

@app.get("/")
def get_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- STAGE 2: IN-MEMORY TASK DATABASE & READ ENDPOINTS ---

tasks_db = [
    {"id": 1, "title": "Setup repository", "done": True},
    {"id": 2, "title": "Build Stage 1 endpoints", "done": True},
    {"id": 3, "title": "Implement Stage 2 endpoints", "done": False}
]

@app.get("/tasks")
def get_all_tasks():
    return tasks_db

@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=404, 
        detail=f"Task {task_id} not found"
    )

# --- STAGE 3 ENDPOINTS ---

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    # Validation: title missing or empty string
    if not task.title or not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required and cannot be empty"
        )
    
    # Auto-increment ID calculation
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    
    new_task = {
        "id": new_id,
        "title": task.title.strip(),
        "done": False
    }
    
    tasks_db.append(new_task)
    return new_task