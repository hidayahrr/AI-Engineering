```
# Task Management REST API
```

```
A clean, lightweight, and containerized CRUD REST API built with **FastAPI**,
**Pydantic**, **Uvicorn**, and **Docker**.
```

# `---` 

# `## Overview` 

```
This project provides a task management backend supporting full CRUD (Create,
Read, Update, Delete) operations with built-in request validation, structured
error handling, OpenAPI (Swagger) documentation, and Docker Compose
orchestration.
```

```
---
```

# `## Project Structure` 

```
```text
AI Engineering/
└── 1-CRUD-API-Python/
    ├── main.py
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── README.md
    └── image_328f53.png
```

```
```
```

```
---
```

# `## Prerequisites` 

```
Ensure you have the following installed on your machine:
```

```
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes
Docker Engine & Docker Compose)
```

```
* [Git](https://git-scm.com/)
```

```
---
```

```
## How to Run the Application
```

```
Navigate to the project subfolder and run the Docker container with a single
command:
```

```
```bash
cd "1-CRUD-API-Python"
docker compose up --build
```

```
```
```

`The server will initialize and listen for incoming HTTP requests at:` 👉 `**`http://localhost:8000`**` 

```
To stop the running application container:
```

```
```bash
docker compose down
```

```
```
```

```
---
```

```
## API Endpoints Reference
```

```
| Method | Endpoint | Description | Status Code |
```

```
| --- | --- | --- | --- |
```

```
| `GET` | `/` | API metadata and available endpoints | `200 OK` |
```

```
| `GET` | `/health` | Server health check endpoint | `200 OK` |
```

```
| `GET` | `/tasks` | Retrieve all tasks in the list | `200 OK` |
```

```
| `GET` | `/tasks/{id}` | Retrieve a specific task by ID | `200 OK` / `404 Not
Found` |
```

```
| `POST` | `/tasks` | Create a new task with validation | `201 Created` / `400
Bad Request` |
```

```
| `PUT` | `/tasks/{id}` | Update title and/or status of a task | `200 OK` / `400
Bad Request` / `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Remove a task by ID | `204 No Content` / `404 Not
Found` |
```

```
---
```

```
## How to Test the API
```

```
You can test the endpoints using PowerShell, Command Prompt, or `curl`.
```

```
### 1. Create a New Task (POST)
```

```
```powershell
```

```
Invoke-RestMethod -Uri "http://localhost:8000/tasks" -Method Post -ContentType
"application/json" -Body '{"title":"Buy milk"}'
```

```
```
```

```
### 2. Retrieve All Tasks (GET)
```

```
```powershell
curl.exe http://localhost:8000/tasks
```

```
```
```

```
### 3. Update a Task (PUT)
```

```
```powershell
```

```
Invoke-RestMethod -Uri "http://localhost:8000/tasks/4" -Method Put -ContentType
"application/json" -Body '{"title":"Buy milk and eggs", "done": true}'
```

```
```
```

```
### 4. Delete a Task (DELETE)
```

```
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks/4" -Method Delete
```

```
```
```

```
---
```

```
## Sample Request & Response Output
```

```
Below is an example HTTP response log generated when creating a valid new task:
```

```
```http
HTTP/1.1 201 Created
date: Fri, 24 Jul 2026 12:00:00 GMT
server: uvicorn
content-length: 42
```

```
content-type: application/json
```

```
{"id":4,"title":"Buy milk","done":false}
```

```
```
```

```
---
```

```
## Interactive Documentation (Swagger UI)
```

```
FastAPI automatically generates interactive OpenAPI documentation. You can test
every endpoint directly from your browser without using terminal commands:
```

👉 `Open **`http://localhost:8000/docs`**` 

```
```
```

```
---
```

```
<ElicitationsGroup message="What would you like to do next?">
<Elicitation label="Commit and push README.md to GitHub" query="Commit and push
README.md to GitHub" query_intent="CLICKABLE_SUGGESTION" />
```

```
<Elicitation label="Add automated pytest unit tests for all endpoints"
query="Add automated pytest unit tests for all endpoints"
query_intent="CLICKABLE_SUGGESTION" />
```

```
<Elicitation label="Add SQLite database persistence using SQLAlchemy" query="Add
SQLite database persistence using SQLAlchemy"
query_intent="CLICKABLE_SUGGESTION" />
</ElicitationsGroup>
```

```
```
```

