from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

from app.main import app
import pytest

from app.db.supabase import supabase
from datetime import datetime, timezone
client = TestClient(app)

@pytest.fixture
def test_transaction_id():
    transaction_id = f"txn_test_{uuid.uuid4().hex}"

    yield transaction_id

    supabase.table("claims").delete().eq(
        "transaction_id", transaction_id
    ).execute()

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_claim(test_transaction_id):
    transaction_id = test_transaction_id

    response = client.post(
        "/claims",
        json={
            "transaction_id": transaction_id,
            "benefit_type": "purchase_protection",
            "amount": 1500.50,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == transaction_id
    assert data["benefit_type"] == "purchase_protection"
    assert Decimal(data["amount"]) == Decimal("1500.50")
    assert data["status"] == "created"

def test_get_claim(test_transaction_id):
    transaction_id = test_transaction_id

    create_response = client.post(
        "/claims",
        json={
            "transaction_id": transaction_id,
            "benefit_type": "purchase_protection",
            "amount": 2000.00,
        },
    )

    assert create_response.status_code == 200

    created_claim = create_response.json()
    claim_id = created_claim["id"]

    get_response = client.get(f"/claims/{claim_id}")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == claim_id
    assert data["transaction_id"] == transaction_id
    assert data["benefit_type"] == "purchase_protection"
    assert Decimal(data["amount"]) == Decimal("2000.00")
    assert data["status"] == "created"

def test_get_claim_not_found():
    fake_claim_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/claims/{fake_claim_id}")

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "CLAIM_NOT_FOUND"
    assert data["message"] == "Claim not found."
    assert "requestId" in data

def test_duplicate_claim(test_transaction_id):
    transaction_id = test_transaction_id

    claim = {
        "transaction_id": transaction_id,
        "benefit_type": "purchase_protection",
        "amount": 1000.00,
    }

    first_response = client.post("/claims", json=claim)

    assert first_response.status_code == 200

    second_response = client.post("/claims", json=claim)

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["code"] == "CLAIM_ALREADY_EXISTS"
    assert data["message"] == (
        "Claim already exists for this transaction and benefit type."
    )
    assert "requestId" in data

def test_create_claim_negative_amount():
    response = client.post(
        "/claims",
        json={
            "transaction_id": f"txn_test_{uuid.uuid4().hex}",
            "benefit_type": "purchase_protection",
            "amount": -500,
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "Request validation failed."
    assert "requestId" in data
    assert len(data["details"]) > 0
    assert data["details"][0]["field"] == "body.amount"

def test_create_claim_invalid_decimal_places():
    response = client.post(
        "/claims",
        json={
            "transaction_id": f"txn_test_{uuid.uuid4().hex}",
            "benefit_type": "purchase_protection",
            "amount": 1500.123,
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert data["message"] == "Request validation failed."
    assert "requestId" in data
    assert len(data["details"]) > 0
    assert data["details"][0]["field"] == "body.amount"

def test_request_id_is_preserved():
    request_id = "req_test_123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id

