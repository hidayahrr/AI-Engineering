import os
import inngest
import inngest.fast_api
from fastapi import FastAPI

# Force local development mode to avoid missing signing key errors
os.environ["INNGEST_DEV"] = "1"

app = FastAPI(title="Background Job API")

# Create Inngest client with ID: report-api
inngest_client = inngest.Inngest(app_id="report-api")

# Define say-hello function triggered by test/hello event
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello_function(ctx: inngest.Context, step: inngest.Step) -> str:
    # Durable sleep step for 5 seconds
    await step.sleep("wait-5-seconds", "5s")
    return "Hello from the background!"

# Serve function on path /api/inngest
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello_function],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
