from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.services.eligibility_service import (
    PURCHASE_PROTECTION,
    RETURN_PROTECTION,
    TRAVEL_DELAY,
    evaluate_benefit,
    evaluate_transaction,
)


def transaction(amount: str, merchant: str = "Apple", currency: str = "usd"):
    return {"amount": Decimal(amount), "merchant": merchant, "currency": currency}


def test_purchase_protection_is_eligible():
    decision = evaluate_transaction(transaction("100"))

    assert decision.eligible is True
    assert decision.benefit_type == PURCHASE_PROTECTION
    assert decision.eligible_amount == Decimal("100")


def test_purchase_protection_is_ineligible_below_threshold():
    decision = evaluate_transaction(transaction("49"))

    assert decision.eligible is False
    assert decision.eligible_amount == Decimal("0.00")


def test_purchase_protection_amount_is_capped():
    decision = evaluate_transaction(transaction("600"))

    assert decision.benefit_type == PURCHASE_PROTECTION
    assert decision.eligible_amount == Decimal("500")


def test_travel_delay_is_eligible_for_airline_transaction():
    decision = evaluate_transaction(transaction("75", merchant="Delta"))

    assert decision.benefit_type == TRAVEL_DELAY
    assert decision.eligible_amount == Decimal("75")


def test_travel_delay_is_ineligible_for_non_airline_merchant():
    decision = evaluate_benefit(
        TRAVEL_DELAY,
        amount=Decimal("75"),
        merchant="Hotel",
        currency="usd",
    )

    assert decision.eligible is False


def test_non_airline_transaction_uses_return_protection():
    decision = evaluate_transaction(transaction("75", merchant="Hotel"))

    assert decision.benefit_type == RETURN_PROTECTION


def test_travel_delay_amount_is_capped():
    decision = evaluate_benefit(
        TRAVEL_DELAY,
        amount=Decimal("350"),
        merchant="Delta",
        currency="usd",
    )

    assert decision.benefit_type == TRAVEL_DELAY
    assert decision.eligible_amount == Decimal("300")


def test_return_protection_is_eligible():
    decision = evaluate_transaction(transaction("75", merchant="Hotel"))

    assert decision.benefit_type == RETURN_PROTECTION


def test_return_protection_is_ineligible_below_threshold():
    decision = evaluate_transaction(transaction("49", merchant="Hotel"))

    assert decision.eligible is False


def test_return_protection_amount_is_capped():
    decision = evaluate_transaction(transaction("275", merchant=""))

    assert decision.benefit_type == RETURN_PROTECTION
    assert decision.eligible_amount == Decimal("250")


def test_non_usd_currency_is_rejected():
    decision = evaluate_transaction(transaction("600", currency="eur"))

    assert decision.eligible is False
    assert decision.reason == "Transaction currency must be USD."


def test_purchase_protection_has_deterministic_priority():
    decision = evaluate_transaction(transaction("150", merchant="Delta"))

    assert decision.benefit_type == PURCHASE_PROTECTION


def test_eligibility_endpoint_returns_decision_schema(monkeypatch):
    from app.api.routes import transactions

    monkeypatch.setattr(
        transactions,
        "get_transaction",
        lambda transaction_id: transaction("600", merchant="Apple"),
    )

    response = TestClient(app).get("/transactions/transaction-123/eligibility")

    assert response.status_code == 200
    assert response.json() == {
        "transactionId": "transaction-123",
        "eligible": True,
        "benefitType": PURCHASE_PROTECTION,
        "eligibleAmount": "500",
        "reason": "Transaction qualifies for purchase protection.",
    }


def test_missing_transaction_returns_structured_404(monkeypatch):
    from app.api.routes import transactions
    from app.core.exceptions import ClaimGuardException

    def transaction_not_found(transaction_id: str):
        raise ClaimGuardException(
            code="TRANSACTION_NOT_FOUND",
            message="Transaction not found.",
            status_code=404,
        )

    monkeypatch.setattr(transactions, "get_transaction", transaction_not_found)

    response = TestClient(app).get("/transactions/missing/eligibility")

    assert response.status_code == 404
    assert response.json()["code"] == "TRANSACTION_NOT_FOUND"
    assert response.json()["message"] == "Transaction not found."
    assert "requestId" in response.json()
