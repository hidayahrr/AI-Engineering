import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.llm.schema import TriageRequest, TriageResponse, CategoryEnum, UrgencyEnum
from src.llm.client import call_llm_with_repair

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


@app.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def triage_ticket(payload: TriageRequest):
    """
    POST Endpoint to classify support tickets.
    When LLM_STUB=0, calls model, parses JSON, validates schema, handles 1 repair retry,
    and logs failures to logs/quarantine.jsonl (returning 422).
    """
    is_stub = os.getenv("LLM_STUB", "0") == "1"

    if is_stub:
        return TriageResponse(
            category=CategoryEnum.bug,
            urgency=UrgencyEnum.high,
            confidence=0.95,
            reason="STUB MODE: Hardcoded valid response satisfying output schema.",
        )

    try:
        # Call LLM with validation & repair loop
        validated_response = call_llm_with_repair(user_input=payload.text)
        return validated_response

    except ValueError as ve:
        # HTTP 422 Unprocessable Entity for schema validation failures
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unhandled internal server error: {str(e)}",
        )