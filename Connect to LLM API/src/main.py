from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.routes.triage import router as triage_router

load_dotenv()

app = FastAPI(
    title="Support Ticket Classifier API",
    description="LLM Integration Endpoint with Schema Validation, Repair Retry, and Quarantine Logging",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0]
    field_name = " -> ".join([str(loc) for loc in first_error["loc"] if loc != "body"])

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": f"Validation failed for field '{field_name}': {first_error['msg']}",
            "invalid_field": field_name,
        },
    )


# Attach the routes defined in src/routes/triage.py
app.include_router(triage_router)