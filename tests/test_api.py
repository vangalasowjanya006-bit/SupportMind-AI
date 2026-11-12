from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from app import graph
from app.database import get_db
from app.main import app
from app.schemas import IntentResult, ResolutionDecision


def test_support_console_is_available():
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Support console" in response.text


def test_customer_details_returns_readable_data(
    seeded_sessionmaker,
):
    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close() 

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get("/customers/C1001/details")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["customer"]["id"] == "C1001"
    assert len(body["transactions"]) == 2
    assert body["cases"] == []


def _tool_call_message(customer_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "lookup_customer",
                "args": {"customer_id": customer_id},
                "id": "call_customer",
            },
            {
                "name": "lookup_transactions",
                "args": {"customer_id": customer_id},
                "id": "call_transactions",
            },
        ],
    )


class _ScriptedLLM:
    def __init__(self, responses):
        self._responses = list(responses)

    def invoke(self, messages):
        return self._responses.pop(0)


def test_support_request_creates_case_and_audit_event(
    monkeypatch,
    seeded_sessionmaker,
):
    from app import tools
    from app.models import AuditEvent, SupportCase

    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)
    monkeypatch.setattr(
        graph,
        "classify_intent",
        lambda message: IntentResult(intent="billing_issue", confidence=0.9),
    )
    monkeypatch.setattr(
        graph,
        "agent_llm",
        _ScriptedLLM([_tool_call_message("C1001"), AIMessage(content="done")]),
    )
    monkeypatch.setattr(
        graph,
        "determine_resolution",
        lambda **kwargs: ResolutionDecision(
            action="no_action",
            reason="No action is required.",
            requires_approval=False,
        ),
    )

    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/support",
            json={"customer_id": "C1001", "message": "I need help"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["approval_status"] == "not_required"

    db = seeded_sessionmaker()
    try:
        case = db.query(SupportCase).filter_by(case_id=body["case_id"]).one()
        assert case.action == "no_action"
        assert db.query(AuditEvent).filter_by(case_db_id=case.id).count() == 1
    finally:
        db.close()


def test_approval_rejection_persists_without_execution(
    monkeypatch,
    seeded_sessionmaker,
):
    from app import tools

    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)
    monkeypatch.setenv("SUPPORT_APPROVER_TOKEN", "test-approver")
    monkeypatch.setattr(
        graph,
        "classify_intent",
        lambda message: IntentResult(intent="refund_request", confidence=0.9),
    )
    monkeypatch.setattr(
        graph,
        "agent_llm",
        _ScriptedLLM([_tool_call_message("C1001"), AIMessage(content="done")]),
    )
    monkeypatch.setattr(
        graph,
        "determine_resolution",
        lambda **kwargs: ResolutionDecision(
            action="refund",
            reason="Duplicate charges require review.",
            requires_approval=True,
        ),
    )

    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        created = client.post(
            "/support",
            json={"customer_id": "C1001", "message": "Refund this charge"},
        )
        case_id = created.json()["case_id"]
        response = client.post(
            f"/cases/{case_id}/approval",
            json={"approved": False},
            headers={"X-Approver-Token": "test-approver"},
        )
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert created.json()["status"] == "awaiting_approval"
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["approval_status"] == "rejected"
    assert "execut" not in response.json()["result"].lower()


def test_approval_requires_approver_credentials(
    monkeypatch,
    seeded_sessionmaker,
):
    from app import tools

    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)
    monkeypatch.setenv("SUPPORT_APPROVER_TOKEN", "test-approver")

    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/cases/CASE-MISSING/approval",
            json={"approved": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_approval_executes_simulated_refund(
    monkeypatch,
    seeded_sessionmaker,
):
    from app.models import SupportCase
    from app import tools

    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)
    monkeypatch.setenv("SUPPORT_APPROVER_TOKEN", "test-approver")
    db = seeded_sessionmaker()
    try:
        case = SupportCase(
            case_id="CASE-APPROVAL",
            customer_id="C1001",
            message="Refund this charge",
            intent="refund_request",
            action="refund",
            reason="Duplicate charges require review.",
            status="awaiting_approval",
            requires_approval=True,
            approval_status="pending",
        )
        db.add(case)
        db.commit()
    finally:
        db.close()

    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/cases/CASE-APPROVAL/approval",
            json={"approved": True},
            headers={"X-Approver-Token": "test-approver"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert body["approval_status"] == "approved"
    assert "simulated refund action executed" in body["result"].lower()


def test_approval_cannot_be_submitted_twice(
    monkeypatch,
    seeded_sessionmaker,
):
    from app import tools

    monkeypatch.setattr(tools, "SessionLocal", seeded_sessionmaker)
    monkeypatch.setenv("SUPPORT_APPROVER_TOKEN", "test-approver")
    db = seeded_sessionmaker()
    try:
        from app.models import SupportCase

        db.add(
            SupportCase(
                case_id="CASE-REJECTED",
                customer_id="C1001",
                message="Refund this charge",
                action="refund",
                status="rejected",
                requires_approval=True,
                approval_status="rejected",
            )
        )
        db.commit()
    finally:
        db.close()

    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/cases/CASE-REJECTED/approval",
            json={"approved": True},
            headers={"X-Approver-Token": "test-approver"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_invalid_support_request_is_rejected():
    response = TestClient(app).post(
        "/support",
        json={"customer_id": "", "message": ""},
    )

    assert response.status_code == 422


def test_model_configuration_failure_returns_service_unavailable(
    monkeypatch,
    seeded_sessionmaker,
):
    def override_get_db():
        db = seeded_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    def fail_graph(_state):
        raise RuntimeError("GOOGLE_API_KEY is not configured")

    monkeypatch.setattr("app.main.support_graph.invoke", fail_graph)
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/support",
            json={"customer_id": "C1001", "message": "I need help"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Support model is not configured"
