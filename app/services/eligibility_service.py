from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


USD = "usd"
PURCHASE_PROTECTION = "PURCHASE_PROTECTION"
TRAVEL_DELAY = "TRAVEL_DELAY"
RETURN_PROTECTION = "RETURN_PROTECTION"

AIRLINE_MERCHANTS = {
    "United Airlines",
    "Delta",
    "American Airlines",
    "Air India",
    "Emirates",
}


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    benefit_type: str | None
    eligible_amount: Decimal
    reason: str


def evaluate_transaction(transaction: Mapping[str, object]) -> EligibilityDecision:
    """Evaluate a transaction against the current synthetic benefit rules."""
    amount = Decimal(str(transaction["amount"]))
    currency = str(transaction["currency"]).lower()
    merchant = str(transaction.get("merchant") or "").strip()

    if currency != USD:
        return _ineligible("Transaction currency must be USD.")

    for benefit_type in (
        PURCHASE_PROTECTION,
        TRAVEL_DELAY,
        RETURN_PROTECTION,
    ):
        decision = evaluate_benefit(
            benefit_type,
            amount=amount,
            merchant=merchant,
            currency=currency,
        )
        if decision.eligible:
            return decision

    return _ineligible(
        "Transaction amount is below the minimum purchase protection threshold."
    )


def evaluate_benefit(
    benefit_type: str,
    *,
    amount: Decimal,
    merchant: str,
    currency: str,
) -> EligibilityDecision:
    """Evaluate one benefit rule independently of the transaction priority."""
    if currency.lower() != USD:
        return _ineligible("Transaction currency must be USD.")

    if benefit_type == PURCHASE_PROTECTION:
        if amount < Decimal("100"):
            return _ineligible(
                "Transaction amount is below the minimum purchase protection threshold."
            )
        if not merchant:
            return _ineligible("Transaction merchant is required for purchase protection.")
        return _eligible(
            PURCHASE_PROTECTION,
            min(amount, Decimal("500")),
            "Transaction qualifies for purchase protection.",
        )

    if benefit_type == TRAVEL_DELAY:
        if merchant not in AIRLINE_MERCHANTS:
            return _ineligible("Transaction merchant is not eligible for travel delay.")
        if amount < Decimal("50"):
            return _ineligible(
                "Transaction amount is below the minimum travel delay threshold."
            )
        return _eligible(
            TRAVEL_DELAY,
            min(amount, Decimal("300")),
            "Transaction qualifies for travel delay protection.",
        )

    if benefit_type == RETURN_PROTECTION:
        if amount < Decimal("50"):
            return _ineligible(
                "Transaction amount is below the minimum return protection threshold."
            )
        return _eligible(
            RETURN_PROTECTION,
            min(amount, Decimal("250")),
            "Transaction qualifies for return protection.",
        )

    raise ValueError(f"Unsupported benefit type: {benefit_type}")


def _eligible(
    benefit_type: str,
    eligible_amount: Decimal,
    reason: str,
) -> EligibilityDecision:
    return EligibilityDecision(True, benefit_type, eligible_amount, reason)


def _ineligible(reason: str) -> EligibilityDecision:
    return EligibilityDecision(False, None, Decimal("0.00"), reason)
