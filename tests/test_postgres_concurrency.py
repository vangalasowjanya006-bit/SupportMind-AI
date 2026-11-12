import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, get_db, get_engine
from app.main import app
from app.models import AuditEvent, SupportCase


def test_postgresql_approval_is_single_execution():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    if not os.getenv("SUPPORT_APPROVER_TOKEN"):
        pytest.skip("SUPPORT_APPROVER_TOKEN is not configured")

    engine = get_engine()
    if engine.dialect.name != "postgresql":
        pytest.skip("This test requires PostgreSQL")

    Base.metadata.create_all(bind=engine)
    case_id = f"CASE-CONCURRENCY-{uuid4().hex[:12].upper()}"
    db = SessionLocal()
    db.add(
        SupportCase(
            case_id=case_id,
            customer_id="C1001",
            message="Refund this charge",
            intent="refund_request",
            action="refund",
            reason="Duplicate charges require review.",
            status="awaiting_approval",
            requires_approval=True,
            approval_status="pending",
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    def submit_approval():
        with TestClient(app) as client:
            response = client.post(
                f"/cases/{case_id}/approval",
                json={"approved": True},
                headers={"X-Approver-Token": os.environ["SUPPORT_APPROVER_TOKEN"]},
            )
            return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: submit_approval(), range(2)))
    finally:
        app.dependency_overrides.clear()

    check = SessionLocal()
    try:
        case = check.query(SupportCase).filter_by(case_id=case_id).one()
        executions = (
            check.query(AuditEvent)
            .filter_by(case_db_id=case.id, event_type="action_executed")
            .count()
        )
        assert sorted(statuses) == [200, 409]
        assert case.status == "resolved"
        assert executions == 1
    finally:
        check.query(AuditEvent).filter(
            AuditEvent.case_db_id == case.id
        ).delete()
        check.delete(case)
        check.commit()
        check.close()
