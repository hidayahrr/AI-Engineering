# Background Job Architecture (FastAPI + Inngest)

A production-grade background job pipeline built with Python, FastAPI, and the Inngest SDK. This system decouples heavy/slow processing from the HTTP request-response cycle using an asynchronous "accept now, process later" pattern.

---

## How to Run locally

### Prerequisites

* Python 3.10+
* Inngest CLI (`inngest.exe` or `npx inngest-cli@latest`)

### 1. Start the FastAPI API Server (Terminal 1)

```powershell
cd Background-Job
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

### 2. Start the Inngest Dev Server (Terminal 2)

```powershell
cd Background-Job
.\inngest.exe dev -u http://localhost:8000/api/inngest
```

Access the Inngest Dashboard at: [**http://localhost:8288**](http://localhost:8288)

## Endpoints & Background Functions

### API Endpoints

| **Method** | **Endpoint**    | **Description**                                                           | **Expected Status**                |
| ---------- | --------------- | ------------------------------------------------------------------------- | ---------------------------------- |
| `GET`      | `/health`       | Server health check endpoint                                              | `200 OK`                           |
| `POST`     | `/reports`      | Triggers report generation; validates input and dispatches background job | `202 Accepted` / `422 Bad Request` |
| `GET`      | `/reports/{id}` | Status endpoint returning report state (`pending`, `done`, `failed`)      | `200 OK` / `404 Not Found`         |

### Inngest Functions

| **Function ID** | **Trigger**         | **Description** |
| --------------- | ------------------- | --------------- |
| `say-hello`     | Event: `test/hello` |                 |

Verification job with a 5-second sleep step

| `make-report` | Event: `report/requested` |   |
| ------------- | ------------------------- | - |

Long-running job (8s sleep) building reports; configured with 2 retries

| `heartbeat` | Cron: `* * * * *` |   |
| ----------- | ----------------- | - |

Scheduled job running every minute to log system state metrics

## Proof of Execution (Stage 2)

### 1. Immediate HTTP 202 Response

```powershell
POST http://localhost:8000/reports
Body: {"topic": "cats"}

Response: HTTP 202 Accepted
{
  "id": "rep-a1b2c3d4",
  "status": "pending",
  "topic": "cats"
}
```

### 2. Polling Status Endpoint

**Initial Poll (Immediate):**

```powershell
GET http://localhost:8000/reports/rep-a1b2c3d4

Response: HTTP 200 OK
{
  "id": "rep-a1b2c3d4",
  "topic": "cats",
  "status": "pending",
  "result": null
}
```

**Second Poll (\~10 seconds later):**

```powershell
GET http://localhost:8000/reports/rep-a1b2c3d4

Response: HTTP 200 OK
{
  "id": "rep-a1b2c3d4",
  "topic": "cats",
  "status": "done",
  "result": "Comprehensive report on cats"
}
```

## Stage 3 & Stage 4 Written Requirements

### Stage 3: Input Validation vs. Job Retries

A bad input (such as an empty topic) must be rejected immediately at the API door with an HTTP 400/422 error because retrying invalid data will never succeed and wastes system resources; automatic retries are reserved for temporary runtime failures like network hiccups or service timeouts.

### Stage 4: Cron Schedules

1. **Every day at 08:00:** `0 8 * * *`

2. **Every Sunday at 22:00:** `0 22 * * 0` (or `0 22 * * 7`)