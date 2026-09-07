from datetime import datetime, timezone

from fastapi.testclient import TestClient
import stripe

from app.api.routes import webhooks
from app.main import app


client = TestClient(app)


def payment_intent_event(metadata=None):
    return {
        "id": "evt_test_payment_intent",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_payment_intent",
                "amount": 129900,
                "currency": "usd",
                "created": int(datetime.now(timezone.utc).timestamp()),
                "metadata": metadata or {},
            }
        },
    }


def configure_webhook_dependencies(monkeypatch, event):
    monkeypatch.setattr(
        webhooks.stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: event,
    )
    monkeypatch.setattr(webhooks, "event_already_processed", lambda event_id: False)
    monkeypatch.setattr(webhooks, "record_webhook_event", lambda **kwargs: kwargs)


def test_payment_intent_with_valid_metadata_creates_transaction(monkeypatch):
    event = payment_intent_event(
        {"customer_id": "cus_test_123", "merchant": "Apple"}
    )
    configure_webhook_dependencies(monkeypatch, event)
    created = {}

    def create_transaction(**kwargs):
        created.update(kwargs)
        return {"id": "transaction-123", **kwargs}

    monkeypatch.setattr(webhooks, "create_transaction", create_transaction)
    monkeypatch.setattr(webhooks, "mark_webhook_processed", lambda event_id: None)

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    assert created["stripe_payment_id"] == "pi_test_payment_intent"
    assert created["customer_id"] == "cus_test_123"
    assert created["merchant"] == "Apple"
    assert created["amount"] == 1299.0


def test_stripe_payment_intent_object_is_supported(monkeypatch):
    event = payment_intent_event(
        {"customer_id": "cus_test_123", "merchant": "Apple"}
    )
    event["data"]["object"] = stripe.PaymentIntent.construct_from(
        event["data"]["object"], "sk_test_123"
    )
    configure_webhook_dependencies(monkeypatch, event)
    created = []
    monkeypatch.setattr(webhooks, "create_transaction", lambda **kwargs: created.append(kwargs))
    monkeypatch.setattr(webhooks, "mark_webhook_processed", lambda event_id: None)

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert len(created) == 1


def test_test_mode_payment_intent_gets_dummy_metadata(monkeypatch):
    event = payment_intent_event()
    event["data"]["object"]["livemode"] = False
    configure_webhook_dependencies(monkeypatch, event)
    created = []
    monkeypatch.setattr(webhooks, "create_transaction", lambda **kwargs: created.append(kwargs))
    monkeypatch.setattr(webhooks, "mark_webhook_processed", lambda event_id: None)

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "received"}
    assert created[0]["customer_id"] == "cus_test_stripe_trigger"
    assert created[0]["merchant"] == "Stripe Test Merchant"


def test_payment_intent_without_customer_id_is_ignored(monkeypatch):
    event = payment_intent_event({"merchant": "Apple"})
    configure_webhook_dependencies(monkeypatch, event)
    ignored = []
    created = []

    monkeypatch.setattr(webhooks, "mark_webhook_ignored", ignored.append)
    monkeypatch.setattr(webhooks, "create_transaction", lambda **kwargs: created.append(kwargs))

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "missing_claimguard_metadata",
    }
    assert ignored == ["evt_test_payment_intent"]
    assert created == []


def test_payment_intent_without_merchant_is_ignored(monkeypatch):
    event = payment_intent_event({"customer_id": "cus_test_123"})
    configure_webhook_dependencies(monkeypatch, event)
    ignored = []
    monkeypatch.setattr(webhooks, "mark_webhook_ignored", ignored.append)
    monkeypatch.setattr(
        webhooks,
        "create_transaction",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not create")),
    )

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert ignored == ["evt_test_payment_intent"]


def test_ignored_event_is_not_marked_as_processed(monkeypatch):
    event = payment_intent_event()
    configure_webhook_dependencies(monkeypatch, event)
    ignored = []
    processed = []
    monkeypatch.setattr(webhooks, "mark_webhook_ignored", ignored.append)
    monkeypatch.setattr(webhooks, "mark_webhook_processed", processed.append)

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert ignored == ["evt_test_payment_intent"]
    assert processed == []


def test_duplicate_webhook_is_not_processed_again(monkeypatch):
    event = payment_intent_event(
        {"customer_id": "cus_test_123", "merchant": "Apple"}
    )
    monkeypatch.setattr(
        webhooks.stripe.Webhook,
        "construct_event",
        lambda payload, signature, secret: event,
    )
    monkeypatch.setattr(webhooks, "event_already_processed", lambda event_id: True)
    monkeypatch.setattr(
        webhooks,
        "create_transaction",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("must not create")),
    )

    response = client.post(
        "/webhooks/stripe",
        content=b"signed-payload",
        headers={"Stripe-Signature": "valid-signature"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "already_processed"}
