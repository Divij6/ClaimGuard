from app.core.exceptions import ClaimGuardException
from decimal import Decimal
from app.db.supabase import supabase
from postgrest.exceptions import APIError

def create_claim(transaction_id: str, benefit_type: str, amount: Decimal):
    claim_data = {
        "transaction_id": transaction_id,
        "benefit_type": benefit_type,
        "amount": str(amount),
        "status": "created",
    }

    try:
        response = supabase.table("claims").insert(claim_data).execute()

        return response.data[0]

    except APIError as error:
        if error.code == "23505":
            raise ClaimGuardException(
                code="CLAIM_ALREADY_EXISTS",
                message="Claim already exists for this transaction and benefit type.",
                status_code=409,
            )

        raise

def get_claim(claim_id: str):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("id", claim_id)
        .execute()
    )

    if not response.data:
        raise ClaimGuardException(
            code="CLAIM_NOT_FOUND",
            message="Claim not found.",
            status_code=404,
        )

    return response.data[0]

def get_claims():
    response = (
        supabase
        .table("claims")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data