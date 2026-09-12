import os
import uuid
import inngest
import inngest.fast_api
from fastapi import FastAPI, status
from pydantic import BaseModel

# Enable local development mode
os.environ["INNGEST_DEV"] = "1"

app = FastAPI(title="Background Job API")

# Initialize Inngest Client
inngest_client = inngest.Inngest(app_id="report-api")


# --- Data Models ---
class ReportRequest(BaseModel):
    user_id: str
    report_type: str


class ReportResponse(BaseModel):
    status: str
    job_id: str


# --- Inngest Functions ---

# Stage 1 function (retained)
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello_function(ctx: inngest.Context, step: inngest.Step) -> str:
    await step.sleep("wait-5-seconds", "5s")
    return "Hello from the background!"


# Stage 2 function: Report generation background worker
@inngest_client.create_function(
    fn_id="generate-report",
    trigger=inngest.TriggerEvent(event="report/generate.requested"),
)
async def generate_report_function(ctx: inngest.Context, step: inngest.Step) -> dict:
    # Access event payload data
    user_id = ctx.event.data.get("user_id", "unknown")
    report_type = ctx.event.data.get("report_type", "standard")

    # Step 1: Simulate report generation processing time
    await step.sleep("simulate-report-generation", "10s")

    # Return completion status summary
    return {
        "status": "completed",
        "user_id": user_id,
        "report_type": report_type,
    }


# Serve Inngest integration containing both functions
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello_function, generate_report_function],
)


# --- FastAPI Endpoint ---
@app.post(
    "/api/reports",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReportResponse,
)
async def create_report(request: ReportRequest):
    job_id = f"job-{uuid.uuid4()}"

    # Send event to Inngest to trigger the background worker asynchronously
    await inngest_client.send(
        inngest.Event(
            name="report/generate.requested",
            data={
                "job_id": job_id,
                "user_id": request.user_id,
                "report_type": request.report_type,
            },
        )
    )

    # Return immediately to caller without waiting for generation to finish
    return ReportResponse(status="pending", job_id=job_id)


@app.get("/health")
def health_check():
    return {"status": "ok"}