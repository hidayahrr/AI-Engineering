from enum import Enum
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# 1. Closed List Enums (Strictly defines allowed categorical values)
# ------------------------------------------------------------------------------

class CategoryEnum(str, Enum):
    """Closed list of allowed categories defined in JOB-CARD.md"""
    billing = "billing"
    bug = "bug"
    feature = "feature"
    other = "other"


class UrgencyEnum(str, Enum):
    """Closed list of allowed urgency levels defined in JOB-CARD.md"""
    low = "low"
    normal = "normal"
    high = "high"


# ------------------------------------------------------------------------------
# 2. Input Validation Schema (Validates incoming HTTP request body)
# ------------------------------------------------------------------------------

class TriageRequest(BaseModel):
    """
    Validates payload sent by the user.
    - Requires 'text' field.
    - Ensures string is between 1 and 2000 characters.
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The customer support message text to be classified."
    )


# ------------------------------------------------------------------------------
# 3. Output Validation Schema (Defines exact contract for endpoint response)
# ------------------------------------------------------------------------------

class TriageResponse(BaseModel):
    """
    Validates output payload returned by the endpoint.
    All category-like fields use Enum closed lists.
    """
    category: CategoryEnum
    urgency: UrgencyEnum
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reason: str = Field(..., description="One short single-sentence justification")