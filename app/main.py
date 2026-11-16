from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from hmac import compare_digest
from os import getenv
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, get_engine
from app import models
from app.database import get_db
from app.graph import support_graph
from app.repositories import (
    add_audit_event,
    create_support_case,
    get_support_case,
    update_case_decision,
)
from app.schemas import ApprovalDecision, SupportRequest, SupportResponse
from app.ui import ui_response


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="SupportMindAI",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def home():
    return ui_response()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": "configured",
    }


@app.get("/customers/{customer_id}/details")
def customer_details(
    customer_id: str,
    db: Session = Depends(get_db),
) -> dict:
    customer = db.scalar(
        select(models.Customer).where(models.Customer.customer_id == customer_id)
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    transactions = list(
        db.scalars(
            select(models.Transaction)
            .where(models.Transaction.customer_db_id == customer.id)
            .order_by(models.Transaction.created_at.desc())
        ).all()
    )
    cases = list(
        db.scalars(
            select(models.SupportCase)
            .where(models.SupportCase.customer_id == customer_id)
            .order_by(models.SupportCase.created_at.desc())
            .limit(10)
        ).all()
    )
    return {
        "customer": {
            "id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status,
        },
        "transactions": [
            {
                "id": transaction.transaction_id,
                "amount": float(transaction.amount),
                "type": transaction.transaction_type,
                "status": transaction.status,
                "created_at": transaction.created_at.isoformat(),
            }
            for transaction in transactions
        ],
        "cases": [
            {
                "id": case.case_id,
                "status": case.status,
                "action": case.action,
                "approval_status": case.approval_status,
                "created_at": case.created_at.isoformat(),
            }
            for case in cases
        ],
    }


def _case_response(case: models.SupportCase) -> SupportResponse:
    return SupportResponse(
        case_id=case.case_id,
        status=case.status,
        intent=case.intent,
        action=case.action,
        reason=case.reason,
        requires_approval=case.requires_approval,
        approval_status=case.approval_status,
        result=case.result,
    )


@app.post("/support", response_model=SupportResponse)
def create_support_request(
    request: SupportRequest,
    db: Session = Depends(get_db),
) -> SupportResponse:
    try:
        result = support_graph.invoke(request.model_dump())
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Support model is not configured",
        ) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Support data is unavailable",
        ) from error

    case_id = f"CASE-{uuid4().hex[:12].upper()}"
    status_value = result.get("status", "failed")
    approval_status = (
        "pending" if result.get("requires_approval") else "not_required"
    )
    try:
        case = create_support_case(
            db,
            case_id=case_id,
            customer_id=request.customer_id,
            message=request.message,
            intent=result.get("intent"),
            action=result.get("action"),
            reason=result.get("reason") or result.get("error"),
            status=status_value,
            requires_approval=bool(result.get("requires_approval")),
            approval_status=approval_status,
        )
        add_audit_event(
            db,
            case,
            event_type="case_created",
            details={"status": status_value, "action": result.get("action")},
        )
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Support case could not be saved",
        ) from error

    return _case_response(case)


@app.get("/cases/{case_id}", response_model=SupportResponse)
def read_support_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> SupportResponse:
    case = get_support_case(db, case_id, for_update=True)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_response(case)


@app.post("/cases/{case_id}/approval", response_model=SupportResponse)
def decide_support_case(
    case_id: str,
    decision: ApprovalDecision,
    db: Session = Depends(get_db),
    approver_token: str | None = Header(default=None, alias="X-Approver-Token"),
) -> SupportResponse:
    configured_token = getenv("SUPPORT_APPROVER_TOKEN")
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Approval service is not configured",
        )
    if not approver_token or not compare_digest(approver_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid approver credentials",
        )

    case = get_support_case(db, case_id, for_update=True)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status != "awaiting_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case is not awaiting approval",
        )

    if not decision.approved:
        update_case_decision(
            db,
            case,
            status="rejected",
            approval_status="rejected",
            result="Sensitive action rejected by an approver.",
        )
        add_audit_event(
            db,
            case,
            event_type="approval_rejected",
            details={"action": case.action},
        )
    else:
        if case.action != "refund":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No supported sensitive action is available",
            )
        update_case_decision(
            db,
            case,
            status="resolved",
            approval_status="approved",
            result=(
                "Simulated refund action executed after approval. "
                "No external billing system was contacted."
            ),
        )
        add_audit_event(
            db,
            case,
            event_type="approval_granted",
            details={"action": case.action},
        )
        add_audit_event(
            db,
            case,
            event_type="action_executed",
            details={"action": case.action, "simulated": True},
        )

    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Approval decision could not be saved",
        ) from error
    return _case_response(case)