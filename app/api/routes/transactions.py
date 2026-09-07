from fastapi import APIRouter

from app.schemas.transactions import TransactionCreate, TransactionResponse
from app.services.transaction_service import create_transaction

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