from app.core.exceptions import ClaimGuardException
from app.services.claim_service import create_claim
from app.services.eligibility_service import evaluate_transaction
from app.services.transaction_service import get_transaction


def start_claim(transaction_id: str):
    """Create a claim using the server-side eligibility decision."""
    transaction = get_transaction(transaction_id)
    decision = evaluate_transaction(transaction)

    if not decision.eligible:
        raise ClaimGuardException(
            code="TRANSACTION_NOT_ELIGIBLE",
            message=decision.reason,
            status_code=422,
        )

    return create_claim(
        transaction_id=transaction_id,
        benefit_type=decision.benefit_type,
        amount=decision.eligible_amount,
    )
