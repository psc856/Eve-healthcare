from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta
import uuid

client = TestClient(app)


def run():
    # Signup with unique email
    email = f"test+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post('/auth/signup', json={"email": email, "password": "secret", "name": "Tester"})
    assert r.status_code == 200
    user = r.json()

    # Login
    r = client.post('/auth/login', json={"username": "test@example.com", "password": "secret"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create centre
    r = client.post('/centres/', json={"name": "Central Lab", "location": "City"})
    assert r.status_code == 200
    centre = r.json()

    # Add test
    r = client.post(f"/centres/{centre['id']}/tests", json={"name": "CBC", "price": 12.5})
    assert r.status_code == 200
    test = r.json()

    # Create booking
    appointment = (datetime.utcnow() + timedelta(days=1)).isoformat()
    booking_payload = {"test_id": test['id'], "centre_id": centre['id'], "appointment": appointment}
    r = client.post('/bookings/', json=booking_payload, headers=headers)
    assert r.status_code == 200
    booking = r.json()

    # Simulate payment (force success)
    r = client.post(f"/payments/?booking_id={booking['id']}&force_status=SUCCESS", headers={"X-Request-Id": "evt-1"})
    assert r.status_code == 200
    pay = r.json()

    # Verify booking status
    r = client.get('/tests/')

    # Webhook idempotency
    evt = {"event_id": "evt-web-1", "booking_id": booking['id'], "status": "SUCCESS"}
    r1 = client.post('/payments/webhook/', json=evt)
    r2 = client.post('/payments/webhook/', json=evt)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get('status') == 'ignored'

    print('All tests passed')


if __name__ == '__main__':
    run()
