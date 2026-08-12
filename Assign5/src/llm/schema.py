from enum import Enum
from pydantic import BaseModel, Field

class CategoryEnum(str, Enum):
    BILLING = "billing"
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"

class UrgencyEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class TriageRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The incoming customer support message text."
    )

class TriageResponse(BaseModel):
    category: CategoryEnum = Field(..., description="Categorization of the support message")
    urgency: UrgencyEnum = Field(..., description="Assessed urgency level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reason: str = Field(..., description="Brief one-sentence explanation for the decision")

def get_stub_response() -> TriageResponse:
    """Returns a deterministic schema-valid response for stub mode testing."""
    return TriageResponse(
        category=CategoryEnum.BUG,
        urgency=UrgencyEnum.HIGH,
        confidence=0.95,
        reason="Stub mode active: Identified login error as a critical bug."
    )
