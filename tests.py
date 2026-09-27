from datetime import datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient

from main import app
from database import create_db


# Make sure database tables exist before running tests
create_db()

client = TestClient(app)


def create_test_user():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "secret123",
            "name": "Test User",
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/auth/login",
        json={
            "username": email,
            "password": "secret123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_signup_and_login():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    signup_response = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "secret123",
            "name": "Test User",
        },
    )

    assert signup_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "username": email,
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_booking_requires_login():
    response = client.post(
        "/bookings/",
        json={
            "test_id": 1,
            "centre_id": 1,
            "appointment": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 401


def test_create_booking_and_payment():
    headers = create_test_user()

    # Create diagnostic centre
    centre_response = client.post(
        "/centres/",
        headers=headers,
        json={
            "name": "Central Lab",
            "location": "Bangalore",
        },
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["id"]

    # Add diagnostic test
    test_response = client.post(
        f"/centres/{centre_id}/tests",
        headers=headers,
        json={
            "name": "CBC",
            "price": 500,
        },
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["id"]

    # Create booking
    appointment = (
        datetime.now(timezone.utc) + timedelta(days=1)
    ).isoformat()

    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment": appointment,
        },
    )

    assert booking_response.status_code == 200

    booking = booking_response.json()

    assert booking["status"] == "PENDING"

    booking_id = booking["id"]

    # Make simulated payment
    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking_id,
            "force_status": "SUCCESS",
        },
    )

    assert payment_response.status_code == 200

    payment = payment_response.json()

    assert payment["status"] == "SUCCESS"


def test_webhook_is_idempotent():
    headers = create_test_user()

    # Create diagnostic centre
    centre_response = client.post(
        "/centres/",
        headers=headers,
        json={
            "name": "Webhook Lab",
            "location": "Bangalore",
        },
    )

    assert centre_response.status_code == 200

    centre_id = centre_response.json()["id"]

    # Add diagnostic test
    test_response = client.post(
        f"/centres/{centre_id}/tests",
        headers=headers,
        json={
            "name": "Blood Test",
            "price": 300,
        },
    )

    assert test_response.status_code == 200

    test_id = test_response.json()["id"]

    # Create booking
    appointment = (
        datetime.now(timezone.utc) + timedelta(days=1)
    ).isoformat()

    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment": appointment,
        },
    )

    assert booking_response.status_code == 200

    booking_id = booking_response.json()["id"]

    # First webhook
    webhook_data = {
        "event_id": f"event_{uuid.uuid4().hex}",
        "booking_id": booking_id,
        "status": "SUCCESS",
    }

    first_response = client.post(
        "/payments/webhook/",
        json=webhook_data,
    )

    assert first_response.status_code == 200

    first_result = first_response.json()

    assert first_result["status"] == "SUCCESS"

    # Send the exact same webhook again
    second_response = client.post(
        "/payments/webhook/",
        json=webhook_data,
    )

    assert second_response.status_code == 200

    second_result = second_response.json()

    # Duplicate event should be ignored
    assert second_result["status"] == "IGNORED"


def test_invalid_booking():
    headers = create_test_user()

    appointment = (
        datetime.now(timezone.utc) + timedelta(days=1)
    ).isoformat()

    response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "test_id": 999999,
            "centre_id": 999999,
            "appointment": appointment,
        },
    )

    assert response.status_code == 404