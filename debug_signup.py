from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def debug():
    r = client.post('/auth/signup', json={"email": "test@example.com", "password": "secret", "name": "Tester"})
    print('status', r.status_code)
    try:
        print('json:', r.json())
    except Exception:
        print('text:', r.text)

if __name__ == '__main__':
    debug()
