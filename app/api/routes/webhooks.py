import os

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from app.services.webhook_service import (
    event_already_processed,
    mark_webhook_processed,
    mark_webhook_ignored,
    record_webhook_event,
)

from datetime import datetime, timezone
from app.services.transaction_service import create_transaction
load_dotenv()
router = APIRouter()

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid payload.",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid signature.",
        )
    event_id = event["id"]
    event_type = event["type"]

    if event_already_processed(event_id):
        print(f"Webhook already processed: {event_id}")
        
        return {"status": "already_processed"}

    record_webhook_event(
        stripe_event_id=event_id,
        event_type=event_type,
    )
    print("Verified Stripe event:")
    print(event_type)

    if event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        payment_intent_data = (
            payment_intent
            if isinstance(payment_intent, dict)
            else payment_intent.to_dict()
        )
        stripe_payment_id = payment_intent_data["id"]
        metadata = payment_intent_data.get("metadata") or {}
        customer_id = metadata.get("customer_id")
        merchant = metadata.get("merchant")

        if payment_intent_data.get("livemode") is False:
            if not customer_id:
                customer_id = "cus_test_stripe_trigger"
            if not merchant:
                merchant = "Stripe Test Merchant"
            if not metadata.get("customer_id") or not metadata.get("merchant"):
                print(
                    "Using dummy ClaimGuard metadata for Stripe test event: "
                    f"event_id={event_id}"
                )

        if not customer_id or not merchant:
            print(
                "Ignoring payment_intent.succeeded event with missing "
                f"ClaimGuard metadata: event_id={event_id}, "
                f"missing_customer_id={not bool(customer_id)}, "
                f"missing_merchant={not bool(merchant)}"
            )
            mark_webhook_ignored(event_id)
            return {
                "status": "ignored",
                "reason": "missing_claimguard_metadata",
            }

        amount = payment_intent_data["amount"] / 100
        currency = payment_intent_data["currency"]
        created_timestamp = payment_intent_data["created"]
        transaction_date = datetime.fromtimestamp(
            created_timestamp,
            tz=timezone.utc,
        )       
        transaction = create_transaction(
            stripe_payment_id=stripe_payment_id,
            customer_id=customer_id,
            merchant=merchant,
            amount=amount,
            currency=currency,
            transaction_date=transaction_date,
        )

        print("Transaction created:")
        print(transaction)

    mark_webhook_processed(event_id)

    return {"status": "received"}
