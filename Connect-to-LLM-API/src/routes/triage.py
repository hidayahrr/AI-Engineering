import os
from fastapi import APIRouter, HTTPException, status
from openai import APIStatusError

from src.llm.schema import TriageRequest, TriageResponse, CategoryEnum, UrgencyEnum
from src.llm.client import call_llm_with_repair

router = APIRouter()


@router.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def triage_ticket(payload: TriageRequest):
    # Requirement 4: Kill switch check
    llm_enabled = os.getenv("LLM_ENABLED", "true").lower() == "true"
    if not llm_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM processing is temporarily disabled via kill switch (LLM_ENABLED=false).",
        )

    is_stub = os.getenv("LLM_STUB", "0") == "1"
    if is_stub:
        return TriageResponse(
            category=CategoryEnum.bug,
            urgency=UrgencyEnum.high,
            confidence=0.95,
            reason="STUB MODE: Hardcoded valid response satisfying output schema.",
        )

    try:
        validated_response = call_llm_with_repair(user_input=payload.text)
        return validated_response

    except TimeoutError as te:
        # Requirement 1: Return 504 on timeout
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM request timed out: {str(te)}",
        )
    except APIStatusError as se:
        # Requirement 2: Fast fail for 401/400/403
        raise HTTPException(
            status_code=se.status_code,
            detail=f"LLM API Error: {se.message}",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unhandled internal server error: {str(e)}",
        )