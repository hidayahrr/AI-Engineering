import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import validation schemas
from src.llm.schema import TriageRequest, TriageResponse, CategoryEnum, UrgencyEnum

# Load environment variables from .env file
load_dotenv()

# Instantiate FastAPI App
app = FastAPI(
    title="Support Ticket Classifier API",
    description="LLM Integration Endpoint with Stub Mode and Schema Validation",
    version="1.0.0"
)

# ------------------------------------------------------------------------------
# Custom HTTP 400 Validation Error Handler
# ------------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Custom error handler ensuring input validation failures return HTTP 400 
    naming the specific field that failed validation (as required by Stage 1).
    """
    errors = exc.errors()
    first_error = errors[0]
    field_name = " -> ".join([str(loc) for loc in first_error["loc"] if loc != "body"])
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "message": f"Validation failed for field '{field_name}': {first_error['msg']}",
            "invalid_field": field_name
        }
    )

# ------------------------------------------------------------------------------
# POST /triage Route (Stage 1 Endpoint)
# ------------------------------------------------------------------------------
@app.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def triage_ticket(payload: TriageRequest):
    """
    POST Endpoint to classify support tickets.
    Checks LLM_STUB environment variable to bypass model calls during testing.
    """
    # Check if STUB mode is enabled (LLM_STUB=1)
    is_stub = os.getenv("LLM_STUB", "0") == "1"

    if is_stub:
        # Return hardcoded schema-compliant object without invoking OpenRouter
        return TriageResponse(
            category=CategoryEnum.bug,
            urgency=UrgencyEnum.high,
            confidence=0.95,
            reason="STUB MODE: Hardcoded valid response satisfying output schema."
        )

    # Note: Real LLM Invocation logic will be wired here in Stage 2
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Real model invocation is not wired yet. Set LLM_STUB=1 in your environment to test stub mode."
    )