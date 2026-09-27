import requests
import uuid
from datetime import datetime, timezone, timedelta

BASE = 'http://127.0.0.1:8000'

def printr(name, r, expect=None):
    ok = (expect is None) or (r.status_code == expect)
    print(f"{name}: {r.status_code} {'OK' if ok else 'FAIL'}")
    try:
        print(r.json())
    except Exception:
        print(r.text[:200])
    print('-'*60)


def run():
    # Docs
    r = requests.get(f"{BASE}/docs")
    printr('GET /docs', r, 200)

    # Centres list
    r = requests.get(f"{BASE}/centres/")
    printr('GET /centres', r, 200)

    # Signup/login
    email = f'verify+{uuid.uuid4().hex[:8]}@example.com'
    r = requests.post(f"{BASE}/auth/signup", json={'email': email, 'password': 'p', 'name': 'V'})
    printr('POST /auth/signup', r, 200)

    r = requests.post(f"{BASE}/auth/login", json={'username': email, 'password': 'p'})
    printr('POST /auth/login', r, 200)
    token = r.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Create centre
    r = requests.post(f"{BASE}/centres/", json={'name': 'Verify Lab', 'location': 'Nowhere'})
    printr('POST /centres', r, 200)
    centre = r.json()

    # List centres
    r = requests.get(f"{BASE}/centres/")
    printr('GET /centres (after create)', r, 200)

    # Add test
    r = requests.post(f"{BASE}/centres/{centre['id']}/tests", json={'name': 'CBC', 'price': 15.0})
    printr('POST /centres/{id}/tests', r, 200)
    test = r.json()

    # List tests
    r = requests.get(f"{BASE}/tests/")
    printr('GET /tests', r, 200)

    # Attempt booking without auth (should fail)
    appointment = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = requests.post(f"{BASE}/bookings/", json={'test_id': test['id'], 'centre_id': centre['id'], 'appointment': appointment})
    printr('POST /bookings without auth', r, 422)

    # Booking with auth
    r = requests.post(f"{BASE}/bookings/", json={'test_id': test['id'], 'centre_id': centre['id'], 'appointment': appointment}, headers=headers)
    printr('POST /bookings with auth', r, 200)
    booking = r.json()

    # Simulate payment
    r = requests.post(f"{BASE}/payments/?booking_id={booking['id']}&force_status=SUCCESS", headers={'X-Request-Id': 'verify-1'})
    printr('POST /payments (simulate)', r, 200)

    # Webhook idempotency
    evt = {'event_id': 'verify-web-1', 'booking_id': booking['id'], 'status': 'SUCCESS'}
    r1 = requests.post(f"{BASE}/payments/webhook/", json=evt)
    printr('POST /payments/webhook (first)', r1, 200)
    r2 = requests.post(f"{BASE}/payments/webhook/", json=evt)
    printr('POST /payments/webhook (second duplicate)', r2, 200)

    print('Verification complete')


if __name__ == '__main__':
    run()
