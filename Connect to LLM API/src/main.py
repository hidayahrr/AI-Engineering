import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import schemas and LLM client
from src.llm.schema import TriageRequest, TriageResponse, CategoryEnum, UrgencyEnum
from src.llm.client import call_llm

load_dotenv()

app = FastAPI(
    title="Support Ticket Classifier API",
    description="LLM Integration Endpoint with Versioned Prompt and OpenRouter Call",
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


@app.post("/triage", status_code=status.HTTP_200_OK)
async def triage_ticket(payload: TriageRequest):
    """
    POST Endpoint to classify support tickets.
    Checks LLM_STUB environment variable.
    When LLM_STUB=0, calls the real OpenRouter API using prompts/triage-v1.md.
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
        # Call the real OpenRouter model via client.py
        raw_llm_response = call_llm(user_input=payload.text)

        # For Stage 2, return raw text response from the model
        return {"raw_response": raw_llm_response}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with LLM provider: {str(e)}",
        )