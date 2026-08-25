import os
from fastapi import APIRouter, HTTPException, status
from src.llm.schema import TriageRequest, TriageResponse, CategoryEnum, UrgencyEnum
from src.llm.client import call_llm_with_repair

router = APIRouter()

@router.post("/triage", response_model=TriageResponse, status_code=status.HTTP_200_OK)
async def triage_ticket(payload: TriageRequest):
    """
    POST Endpoint to classify support tickets.
    Located in src/routes/triage.py per blueprint structure.
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
        validated_response = call_llm_with_repair(user_input=payload.text)
        return validated_response
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