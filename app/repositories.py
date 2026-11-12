import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, Customer, SupportCase, Transaction


def get_customer_by_customer_id(
    db: Session,
    customer_id: str,
) -> Customer | None:
    statement = select(Customer).where(
        Customer.customer_id == customer_id
    )

    return db.scalar(statement)


def get_transactions_by_customer_id(
    db: Session,
    customer_id: str,
) -> list[Transaction]:
    statement = (
        select(Transaction)
        .join(Customer)
        .where(Customer.customer_id == customer_id)
        .order_by(Transaction.created_at.desc())
    )

    return list(db.scalars(statement).all())


def create_support_case(
    db: Session,
    *,
    case_id: str,
    customer_id: str,
    message: str,
    intent: str | None,
    action: str | None,
    reason: str | None,
    status: str,
    requires_approval: bool,
    approval_status: str,
) -> SupportCase:
    case = SupportCase(
        case_id=case_id,
        customer_id=customer_id,
        message=message,
        intent=intent,
        action=action,
        reason=reason,
        status=status,
        requires_approval=requires_approval,
        approval_status=approval_status,
    )
    db.add(case)
    db.flush()
    return case


def get_support_case(
    db: Session,
    case_id: str,
    *,
    for_update: bool = False,
) -> SupportCase | None:
    statement = select(SupportCase).where(SupportCase.case_id == case_id)
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def update_case_decision(
    db: Session,
    case: SupportCase,
    *,
    status: str,
    approval_status: str | None = None,
    result: str | None = None,
) -> SupportCase:
    case.status = status
    if approval_status is not None:
        case.approval_status = approval_status
    if result is not None:
        case.result = result
    case.updated_at = datetime.now(timezone.utc)
    db.flush()
    return case


def add_audit_event(
    db: Session,
    case: SupportCase,
    *,
    event_type: str,
    details: dict[str, str | bool | None],
) -> AuditEvent:
    event = AuditEvent(
        case_db_id=case.id,
        event_type=event_type,
        details=json.dumps(details),
    )
    db.add(event)
    db.flush()
    return event