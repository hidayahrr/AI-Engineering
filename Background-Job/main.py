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

# In-memory database dictionary for report status tracking
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


# Stage 2 & 3 Function: Report generator with explicit retry limit (retries=2)
@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,  # Exactly 2 retries (3 attempts total)
)
async def make_report_function(ctx: inngest.Context, step: inngest.Step) -> dict:
    report_id = ctx.event.data.get("id")
    topic = ctx.event.data.get("topic", "")

    # Step 1: Simulate slow background processing (8 seconds)
    await step.sleep("do-the-slow-work", "8s")

    # Step 2: Build report and update state in database
    async def build_report():
        # Stage 3 Failure Simulation: Throw error if topic is "fail"
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


# Serve Inngest functions
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello_function, make_report_function],
)


# --- FastAPI Endpoints ---

# POST /reports - Initiates background report job
@app.post(
    "/reports",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportResponse,
)
async def create_report(request: ReportRequest):
    # Stage 3 Input Validation: Reject empty or whitespace-only topics
    clean_topic = request.topic.strip()
    if not clean_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic cannot be empty",
        )

    report_id = f"rep-{uuid.uuid4().hex[:8]}"

    # Save initial pending state
    reports_db[report_id] = {
        "id": report_id,
        "topic": clean_topic,
        "status": "pending",
        "result": None,
    }

    # Dispatch event to Inngest
    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": clean_topic,
            },
        )
    )

    # Return immediate 202 Accepted response
    return ReportResponse(
        id=report_id,
        status="pending",
        topic=clean_topic,
    )


# GET /reports/{report_id} - Status endpoint
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