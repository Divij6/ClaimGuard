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


class EligibilityResponse(BaseModel):
    transaction_id: str = Field(serialization_alias="transactionId")
    eligible: bool
    benefit_type: str | None = Field(serialization_alias="benefitType")
    eligible_amount: Decimal = Field(serialization_alias="eligibleAmount")
    reason: str
