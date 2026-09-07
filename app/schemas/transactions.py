from decimal import Decimal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    stripe_payment_id: str
    customer_id: str
    merchant: str
    amount: Decimal = Field(
        ge=0,
        decimal_places=2,
    )
    currency: str
    transaction_date: datetime


class TransactionResponse(BaseModel):
    id: UUID
    stripe_payment_id: str
    customer_id: str
    merchant: str
    amount: Decimal
    currency: str
    transaction_date: datetime
    created_at: datetime