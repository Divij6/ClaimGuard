from typing import List

from fastapi import APIRouter

from app.schemas.transactions import (
    EligibilityResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.eligibility_service import evaluate_transaction
from app.services.claim_initiation_service import start_claim
from app.services.transaction_service import (
    create_transaction,
    get_transaction,
    get_transactions,
)
from app.schemas.claims import ClaimResponse

router = APIRouter()


@router.post("/transactions", response_model=TransactionResponse)
def create_transaction_endpoint(transaction: TransactionCreate):
    return create_transaction(
        stripe_payment_id=transaction.stripe_payment_id,
        customer_id=transaction.customer_id,
        merchant=transaction.merchant,
        amount=transaction.amount,
        currency=transaction.currency,
        transaction_date=transaction.transaction_date,
    )


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions_endpoint():
    return get_transactions()


@router.get(
    "/transactions/{transaction_id}/eligibility",
    response_model=EligibilityResponse,
)
def get_transaction_eligibility(transaction_id: str):
    transaction = get_transaction(transaction_id)
    decision = evaluate_transaction(transaction)

    return EligibilityResponse(
        transaction_id=transaction_id,
        eligible=decision.eligible,
        benefit_type=decision.benefit_type,
        eligible_amount=decision.eligible_amount,
        reason=decision.reason,
    )


@router.post("/transactions/{transaction_id}/claim", response_model=ClaimResponse)
def start_claim_endpoint(transaction_id: str):
    return start_claim(transaction_id)
