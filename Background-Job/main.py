import os
import uuid
import inngest
import inngest.fast_api
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Enable local development mode
os.environ["INNGEST_DEV"] = "1"

app = FastAPI(title="Background Job API")

# Initialize Inngest Client
inngest_client = inngest.Inngest(app_id="report-api")

# In-memory database dictionary
reports_db = {}


# --- Data Models ---
class ReportRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Report topic cannot be empty")


class ReportResponse(BaseModel):
    id: str
    status: str
    topic: str


# --- Inngest Functions ---

# Stage 1 Function
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello_function(ctx: inngest.Context, step: inngest.Step) -> str:
    await step.sleep("wait-5-seconds", "5s")
    return "Hello from the background!"


# Stage 2 & 3 Function: Report generator
@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
)
async def make_report_function(ctx: inngest.Context, step: inngest.Step) -> dict:
    report_id = ctx.event.data.get("id")
    topic = ctx.event.data.get("topic", "")

    await step.sleep("do-the-slow-work", "8s")

    async def build_report():
        if topic.lower() == "fail":
            if report_id in reports_db:
                reports_db[report_id]["status"] = "failed"
            raise Exception("The report oven is broken!")

        result_text = f"Comprehensive report on {topic}"
        if report_id in reports_db:
            reports_db[report_id]["status"] = "done"
            reports_db[report_id]["result"] = result_text

        return {"status": "done", "result": result_text}

    return await step.run("build-report", build_report)


# Stage 4 Function: Cron Heartbeat (Runs every minute)
@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),  # Every minute schedule
)
async def heartbeat_function(ctx: inngest.Context, step: inngest.Step) -> dict:
    async def log_summary():
        # Count report statuses across in-memory database
        pending_count = sum(1 for r in reports_db.values() if r["status"] == "pending")
        done_count = sum(1 for r in reports_db.values() if r["status"] == "done")
        failed_count = sum(1 for r in reports_db.values() if r["status"] == "failed")

        summary = f"HEARTBEAT SUMMARY: Pending={pending_count}, Done={done_count}, Failed={failed_count}"
        print(summary)
        return {"summary": summary}

    return await step.run("log-system-status", log_summary)


# Serve all 3 functions to Inngest
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello_function, make_report_function, heartbeat_function],
)


# --- FastAPI Endpoints ---
@app.post(
    "/reports",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportResponse,
)
async def create_report(request: ReportRequest):
    clean_topic = request.topic.strip()
    if not clean_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic cannot be empty",
        )

    report_id = f"rep-{uuid.uuid4().hex[:8]}"

    reports_db[report_id] = {
        "id": report_id,
        "topic": clean_topic,
        "status": "pending",
        "result": None,
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": clean_topic,
            },
        )
    )

    return ReportResponse(
        id=report_id,
        status="pending",
        topic=clean_topic,
    )


@app.get("/reports/{report_id}")
async def get_report_status(report_id: str):
    if report_id not in reports_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report ID not found",
        )

    return reports_db[report_id]


@app.get("/health")
def health_check():
    return {"status": "ok"}