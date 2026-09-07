from decimal import Decimal
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.supabase import supabase


client = TestClient(app)


@pytest.fixture
def test_stripe_payment_id():
    stripe_payment_id = f"pi_test_{uuid.uuid4().hex}"

    yield stripe_payment_id

    supabase.table("transactions").delete().eq(
        "stripe_payment_id", stripe_payment_id
    ).execute()

def test_create_transaction(test_stripe_payment_id):
    transaction_id = test_stripe_payment_id

    response = client.post(
        "/transactions",
        json={
            "stripe_payment_id": transaction_id,
            "customer_id": "cus_test_123",
            "merchant": "Apple",
            "amount": 1299.00,
            "currency": "USD",
            "transaction_date": "2026-09-07T12:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stripe_payment_id"] == transaction_id
    assert data["customer_id"] == "cus_test_123"
    assert data["merchant"] == "Apple"
    assert Decimal(data["amount"]) == Decimal("1299.00")
    assert data["currency"] == "USD"
    assert "id" in data
    assert "created_at" in data