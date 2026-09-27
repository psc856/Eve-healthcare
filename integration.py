import requests
from datetime import datetime, timezone, timedelta
import uuid

BASE = 'http://127.0.0.1:8000'


def expect(resp, code=200):
    print(resp.status_code, resp.text)
    if resp.status_code != code:
        raise SystemExit(f'Expected {code}, got {resp.status_code}')


def run():
    email = f'integ+{uuid.uuid4().hex[:8]}@example.com'
    print('SIGNUP', email)
    r = requests.post(f'{BASE}/auth/signup', json={'email': email, 'password': 'pass', 'name': 'Integ'})
    expect(r, 200)

    print('LOGIN')
    r = requests.post(f'{BASE}/auth/login', json={'username': email, 'password': 'pass'})
    expect(r, 200)
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    print('CREATE CENTRE')
    r = requests.post(f'{BASE}/centres/', json={'name': 'Integ Lab', 'location': 'Test City'})
    expect(r, 200)
    centre = r.json()

    print('ADD TEST')
    r = requests.post(f"{BASE}/centres/{centre['id']}/tests", json={'name': 'Glucose', 'price': 25.0})
    expect(r, 200)
    test = r.json()

    print('BOOKING')
    appointment = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = requests.post(f'{BASE}/bookings/', json={'test_id': test['id'], 'centre_id': centre['id'], 'appointment': appointment}, headers=headers)
    expect(r, 200)
    booking = r.json()

    print('SIMULATE PAYMENT (force SUCCESS)')
    r = requests.post(f"{BASE}/payments/?booking_id={booking['id']}&force_status=SUCCESS", headers={'X-Request-Id': 'evt-0001'})
    expect(r, 200)

    print('WEBHOOK IDEMPOTENCY')
    evt = {'event_id': 'web-evt-1', 'booking_id': booking['id'], 'status': 'SUCCESS'}
    r1 = requests.post(f'{BASE}/payments/webhook/', json=evt)
    expect(r1, 200)
    r2 = requests.post(f'{BASE}/payments/webhook/', json=evt)
    expect(r2, 200)
    print('Second webhook response:', r2.json())

    print('Integration complete')


if __name__ == '__main__':
    run()
