from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field


class ClaimCreate(BaseModel):
    transaction_id: str
    benefit_type: str
    amount: Decimal = Field(ge=0, decimal_places=2)


class ClaimResponse(BaseModel):
    id: UUID
    transaction_id: str
    benefit_type: str
    amount: Decimal
    status: str
    created_at: datetime