from dotenv import load_dotenv

from app.schemas import IntentResult

load_dotenv()

INTENT_SYSTEM_PROMPT = """
You are an intent classification component in an enterprise customer support system.

Classify the customer's primary intent into exactly one of these categories:

- billing_issue: charges, payments, invoices, duplicate charges, or billing problems
- refund_request: the customer explicitly asks for money to be refunded
- technical_issue: application, service, or functionality problems
- account_issue: login, authentication, account access, or profile problems
- unknown: the request cannot be reliably classified

Return only the structured result required by the schema.
"""

def classify_intent(message: str) -> IntentResult:
    from app.llm import get_chat_model

    return get_chat_model().with_structured_output(IntentResult).invoke(
        [
            ("system", INTENT_SYSTEM_PROMPT),
            ("human", message),
        ]
    )