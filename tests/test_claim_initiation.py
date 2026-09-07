from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ClaimGuardException
from app.main import app
from app.services.eligibility_service import EligibilityDecision, PURCHASE_PROTECTION
from app.services import claim_initiation_service


def eligible_transaction():
    return {"amount": Decimal("1299"), "merchant": "Apple", "currency": "usd"}


def created_claim(transaction_id: str):
    return {
        "id": uuid4(),
        "transaction_id": transaction_id,
        "benefit_type": PURCHASE_PROTECTION,
        "amount": Decimal("500.00"),
        "status": "created",
        "created_at": datetime.now(timezone.utc),
    }


def test_eligible_transaction_starts_claim_with_eligibility_values(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        claim_initiation_service,
        "get_transaction",
        lambda _: eligible_transaction(),
    )
    monkeypatch.setattr(
        claim_initiation_service,
        "evaluate_transaction",
        lambda _: EligibilityDecision(
            True,
            PURCHASE_PROTECTION,
            Decimal("500.00"),
            "Eligible.",
        ),
    )

    def create(transaction_id: str, benefit_type: str, amount: Decimal):
        captured.update(
            transaction_id=transaction_id,
            benefit_type=benefit_type,
            amount=amount,
        )
        return created_claim(transaction_id)

    monkeypatch.setattr(claim_initiation_service, "create_claim", create)

    result = claim_initiation_service.start_claim("transaction-123")

    assert result["status"] == "created"
    assert captured == {
        "transaction_id": "transaction-123",
        "benefit_type": PURCHASE_PROTECTION,
        "amount": Decimal("500.00"),
    }


def test_ineligible_transaction_does_not_create_claim(monkeypatch):
    monkeypatch.setattr(
        claim_initiation_service,
        "get_transaction",
        lambda _: eligible_transaction(),
    )
    monkeypatch.setattr(
        claim_initiation_service,
        "evaluate_transaction",
        lambda _: EligibilityDecision(False, None, Decimal("0.00"), "Not eligible."),
    )
    def should_not_create(*args, **kwargs):
        raise AssertionError("A claim must not be created for an ineligible transaction.")

    monkeypatch.setattr(claim_initiation_service, "create_claim", should_not_create)
    with pytest.raises(ClaimGuardException) as error:
        claim_initiation_service.start_claim("transaction-123")

    assert error.value.code == "TRANSACTION_NOT_ELIGIBLE"
    assert error.value.status_code == 422


def test_missing_transaction_is_preserved(monkeypatch):
    def missing_transaction(_: str):
        raise ClaimGuardException("TRANSACTION_NOT_FOUND", "Transaction not found.", 404)

    monkeypatch.setattr(claim_initiation_service, "get_transaction", missing_transaction)

    with pytest.raises(ClaimGuardException) as error:
        claim_initiation_service.start_claim("missing")

    assert error.value.code == "TRANSACTION_NOT_FOUND"


def test_duplicate_claim_error_is_preserved(monkeypatch):
    monkeypatch.setattr(
        claim_initiation_service,
        "get_transaction",
        lambda _: eligible_transaction(),
    )
    monkeypatch.setattr(
        claim_initiation_service,
        "evaluate_transaction",
        lambda _: EligibilityDecision(True, PURCHASE_PROTECTION, Decimal("500"), "Eligible."),
    )

    def duplicate_claim(*args, **kwargs):
        raise ClaimGuardException(
            "CLAIM_ALREADY_EXISTS",
            "Claim already exists for this transaction and benefit type.",
            409,
        )

    monkeypatch.setattr(claim_initiation_service, "create_claim", duplicate_claim)

    with pytest.raises(ClaimGuardException) as error:
        claim_initiation_service.start_claim("transaction-123")

    assert error.value.code == "CLAIM_ALREADY_EXISTS"
    assert error.value.status_code == 409


def test_claim_endpoint_ignores_client_supplied_benefit_and_amount(monkeypatch):
    from app.api.routes import transactions

    monkeypatch.setattr(
        transactions,
        "start_claim",
        lambda transaction_id: created_claim(transaction_id),
    )

    response = TestClient(app).post(
        "/transactions/transaction-123/claim",
        json={"benefit_type": "ARBITRARY", "amount": "999999.99"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["benefit_type"] == PURCHASE_PROTECTION
    assert data["amount"] == "500.00"


@pytest.mark.parametrize(
    ("error", "status_code", "code", "message"),
    [
        (
            ClaimGuardException("TRANSACTION_NOT_ELIGIBLE", "Not eligible.", 422),
            422,
            "TRANSACTION_NOT_ELIGIBLE",
            "Not eligible.",
        ),
        (
            ClaimGuardException("TRANSACTION_NOT_FOUND", "Transaction not found.", 404),
            404,
            "TRANSACTION_NOT_FOUND",
            "Transaction not found.",
        ),
        (
            ClaimGuardException(
                "CLAIM_ALREADY_EXISTS",
                "Claim already exists for this transaction and benefit type.",
                409,
            ),
            409,
            "CLAIM_ALREADY_EXISTS",
            "Claim already exists for this transaction and benefit type.",
        ),
    ],
)
def test_claim_endpoint_returns_structured_business_errors(
    monkeypatch,
    error,
    status_code,
    code,
    message,
):
    from app.api.routes import transactions

    def raise_error(_: str):
        raise error

    monkeypatch.setattr(transactions, "start_claim", raise_error)

    response = TestClient(app).post("/transactions/transaction-123/claim")

    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert response.json()["message"] == message
    assert "requestId" in response.json()
