from fastapi import APIRouter
from app.schemas.claims import ClaimCreate, ClaimResponse
from app.services.claim_service import create_claim
from app.services.claim_service import create_claim, get_claim, get_claims
from typing import List
router = APIRouter()


@router.post("/claims", response_model=ClaimResponse)
def create_claim_endpoint(claim: ClaimCreate):
    return create_claim(
        transaction_id=claim.transaction_id,
        benefit_type=claim.benefit_type,
        amount=claim.amount
    )

@router.get("/claims/{claim_id}", response_model=ClaimResponse)
def get_claim_endpoint(claim_id: str):
    return get_claim(claim_id)

@router.get("/claims", response_model=List[ClaimResponse])
def get_claims_endpoint():
    return get_claims()