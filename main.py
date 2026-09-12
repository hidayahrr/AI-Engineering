import os
import inngest
import inngest.fast_api
from fastapi import FastAPI

# Enable local dev mode
os.environ["INNGEST_DEV"] = "1"

app = FastAPI(title="Background Job API")

inngest_client = inngest.Inngest(app_id="report-api")

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello_function(ctx: inngest.Context, step: inngest.Step) -> str:
    await step.sleep("wait-5-seconds", "5s")
    return "Hello from the background!"

inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello_function],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
