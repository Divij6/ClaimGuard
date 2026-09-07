from decimal import Decimal

from postgrest.exceptions import APIError

from app.core.exceptions import ClaimGuardException
from app.db.supabase import supabase


def create_transaction(
    stripe_payment_id: str,
    customer_id: str,
    merchant: str,
    amount: Decimal,
    currency: str,
    transaction_date,
):
    transaction_data = {
        "stripe_payment_id": stripe_payment_id,
        "customer_id": customer_id,
        "merchant": merchant,
        "amount": str(amount),
        "currency": currency,
        "transaction_date": transaction_date.isoformat(),
    }

    try:
        response = (
            supabase
            .table("transactions")
            .insert(transaction_data)
            .execute()
        )

        return response.data[0]

    except APIError as error:
        if error.code == "23505":
            raise ClaimGuardException(
                code="TRANSACTION_ALREADY_EXISTS",
                message="Transaction already exists for this Stripe payment.",
                status_code=409,
            )

        raise


def get_transaction(transaction_id: str):
    response = (
        supabase
        .table("transactions")
        .select("*")
        .eq("id", transaction_id)
        .execute()
    )

    if not response.data:
        raise ClaimGuardException(
            code="TRANSACTION_NOT_FOUND",
            message="Transaction not found.",
            status_code=404,
        )

    return response.data[0]


def get_transactions():
    response = (
        supabase
        .table("transactions")
        .select("*")
        .order("transaction_date", desc=True)
        .execute()
    )

    return response.data
