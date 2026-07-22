from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Item Data Model (Existing)
class Item(BaseModel):
    name: str
    description: str | None = None

# Database Simulation (Item)
db = {}

# --- STAGE 2: IN-MEMORY TASK DATABASE ---
tasks_db = [
    {"id": 1, "title": "Setup repository", "done": True},
    {"id": 2, "title": "Build Stage 1 endpoints", "done": True},
    {"id": 3, "title": "Implement Stage 2 endpoints", "done": False}
]

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

# --- STAGE 2 ENDPOINTS ---

# 1. GET /tasks (Return full task list)
@app.get("/tasks")
def get_all_tasks():
    return tasks_db

# 2. GET /tasks/{task_id} (Return single task or 404)
@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    
    raise HTTPException(
        status_code=404, 
        detail=f"Task {task_id} not found"
    )

# --- EXISTING ITEM ENDPOINTS ---

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