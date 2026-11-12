# Srize Agentic Support

Srize Agentic Support is a FastAPI application that analyzes customer-support
requests, retrieves customer and transaction information from PostgreSQL,
recommends a resolution with Google Gemini, and persists the resulting support
case and audit events.

The project includes a lightweight browser support console and an approval
workflow for higher-value simulated refunds.

## What it solves

Support agents often need to combine a customer's message with account and
billing records before deciding whether to resolve, escalate, or request
approval. This project demonstrates that workflow with structured model output,
LangGraph orchestration, deterministic refund checks, persistence, and human
approval.

## Implemented features

- FastAPI API and browser support console.
- Google Gemini intent classification and resolution reasoning.
- Structured Pydantic outputs for intent and resolution decisions.
- LangGraph tool-calling workflow.
- PostgreSQL persistence through SQLAlchemy and Psycopg.
- Customer and transaction lookup tools.
- Duplicate completed-transaction validation before refunds.
- Automatic resolution for eligible low-value duplicate refunds.
- Approval and rejection workflow for sensitive or higher-value actions.
- Shared-token approver authentication through `X-Approver-Token`.
- Support-case and audit-event persistence.
- PostgreSQL row locking for serialized approval decisions.
- Readable customer details and case result views.
- SQLite-backed automated tests and a PostgreSQL concurrency test that skips
  when PostgreSQL is unavailable.

Actions are simulated. The application does not contact a billing provider.

## Technology stack

- Python 3.10+
- FastAPI and Uvicorn
- LangGraph and LangChain Core
- Google Gemini through `langchain-google-genai`
- Pydantic
- SQLAlchemy and Psycopg
- PostgreSQL
- Pytest
- Docker Compose for local PostgreSQL

## Architecture

```text
Browser or API client
        |
        v
FastAPI request validation
        |
        v
LangGraph workflow
  classify intent
        |
  Gemini tool-calling agent
        |
  customer and transaction tools
        |
  deterministic evidence validation
        |
  Gemini resolution decision
        |
  approval or finalization
        |
        v
SupportCase + AuditEvent in PostgreSQL
```

## Agent workflow

The graph in `app/graph.py` executes:

```text
START
  -> classify_intent
  -> agent
  -> tools <-> agent
  -> extract_data
  -> reason
  -> await_approval OR finalize
  -> END
```

The agent must retrieve customer and transaction data through tools. Refund
decisions are then checked deterministically against completed duplicate
transactions. If refund evidence is absent, the request is escalated instead
of being executed.

## Project structure

```text
Enterprise-Agentic-Support/
├── app/
│   ├── database.py       # SQLAlchemy engine and session lifecycle
│   ├── graph.py          # LangGraph workflow and deterministic checks
│   ├── intent.py         # Structured Gemini intent classification
│   ├── llm.py            # Lazy Gemini model configuration
│   ├── main.py           # FastAPI app, API routes, and approval handling
│   ├── models.py         # Customer, transaction, case, and audit models
│   ├── reasoning.py      # Structured Gemini resolution reasoning
│   ├── repositories.py   # Database access helpers
│   ├── schemas.py        # Request and response schemas
│   ├── state.py          # LangGraph state definition
│   ├── tools.py          # Customer and transaction tools
│   └── ui.py             # Server-rendered support console
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_graph.py
│   ├── test_postgres_concurrency.py
│   └── test_tools.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

Generated caches such as `.venv/`, `__pycache__/`, and `.pytest_cache/` are
local-only and excluded by `.gitignore`.

## Setup on Windows

Create and activate a virtual environment:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set real local values. Never commit `.env`.
At minimum configure:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/DATABASE
GOOGLE_API_KEY=your-key
GEMINI_MODEL=gemini-3.5-flash-lite
SUPPORT_APPROVER_TOKEN=local-secret
```

The database URL must URL-encode special characters in the password. For
example, an `@` in a password must be represented as `%40`.

## PostgreSQL

The included Compose file starts PostgreSQL with the host port `5432`:

```powershell
docker compose up -d postgres
```

Set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` to match the
database URL. The application creates its SQLAlchemy tables during startup.
No migration framework is currently included.

## Running the application

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- Browser console: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health response |
| POST | `/support` | Analyze a customer support request and create a case |
| GET | `/customers/{customer_id}/details` | Read customer, transaction, and recent case details |
| GET | `/cases/{case_id}` | Retrieve a support case |
| POST | `/cases/{case_id}/approval` | Approve or reject a pending case |

Example request:

```powershell
$body = @{
  customer_id = "C3005"
  message = "I was charged twice for my annual subscription. Please refund the duplicate charge."
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/support `
  -ContentType "application/json" `
  -Body $body
```

The response contains a `case_id`, status, classified intent, recommended
action, reason, approval state, and result.

## Approval workflow

Duplicate refunds are accepted only when completed duplicate transactions are
verified. A higher-value duplicate refund can return:

```json
{
  "status": "awaiting_approval",
  "action": "refund",
  "requires_approval": true,
  "approval_status": "pending"
}
```

Submit an approval decision with the configured token:

```powershell
$headers = @{ "X-Approver-Token" = "your-local-token" }
$body = '{"approved":true}'

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/cases/CASE-ID/approval `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Approval marks the simulated refund as `resolved` and records
`approval_granted` and `action_executed` audit events. Rejection marks the case
as `rejected` and records `approval_rejected`. A second decision returns
`409 Conflict`.

## Database and audit logging

The application defines:

- `customers`
- `transactions`
- `support_cases`
- `audit_events`

`SupportCase` stores the request, decision, status, approval state, and result.
`AuditEvent` records case creation, approval/rejection, and simulated action
execution.

## Testing

Run the isolated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The latest local verification completed with **16 passed and 1 skipped**. The
skipped test is the PostgreSQL concurrency test when PostgreSQL configuration
is unavailable.

Additional checks:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app tests
git diff --check
```

## Security considerations and limitations

- `.env` contains local secrets and must remain untracked.
- Approval uses one shared token; it is not user identity, role-based access,
  or production authentication.
- No migration system is included.
- Refund execution is simulated and does not call an external billing system.
- Gemini availability, model permissions, API quotas, and network access can
  affect requests.
- The server-rendered UI is intentionally lightweight and does not replace a
  production frontend or authentication layer.

## Future improvements

- Add migrations with Alembic.
- Replace shared-token approval with authenticated users and roles.
- Add policy retrieval/RAG with evaluated source citations.
- Add production observability, tracing, rate limiting, and structured logs.
- Add a real billing-provider adapter behind an explicit execution boundary.
- Add broader evaluation cases and a managed deployment configuration.



## License

No license is declared for this repository at present. All rights remain with
the applicable copyright holders. See the ownership and attribution section
above before redistributing the project.
