from typing import Literal

from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent: Literal[
        "billing_issue",
        "refund_request",
        "technical_issue",
        "account_issue",
        "unknown",
    ]
    confidence: float = Field(ge=0.0, le=1.0)


class ResolutionDecision(BaseModel):
    action: Literal[
        "refund",
        "request_more_information",
        "escalate",
        "no_action",
    ]
    reason: str
    requires_approval: bool


class SupportRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=50)
    message: str = Field(min_length=1, max_length=10_000)


class SupportResponse(BaseModel):
    case_id: str
    status: str
    intent: str | None = None
    action: str | None = None
    reason: str | None = None
    requires_approval: bool = False
    approval_status: str = "not_required"
    result: str | None = None


class ApprovalDecision(BaseModel):
    approved: bool