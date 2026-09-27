EVE Healthcare - Demo Backend

Minimal FastAPI backend for diagnostic test bookings with simulated payments.

Run locally:

1. Create virtualenv and install:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start server:

```bash
uvicorn main:app --reload

Run with Docker:

```
docker build -t eve-healthcare:local .
docker run -p 8000:8000 -e DATABASE_URL="sqlite:///./dev.db" eve-healthcare:local
```

Or using docker-compose:

```
docker-compose up --build
```
```

API highlights:
- `POST /auth/signup` - create user
- `POST /auth/login` - obtain JWT (use OAuth2 password)
- `POST /centres/` - create centre
- `POST /centres/{id}/tests` - add test to centre
- `GET /tests/` - list tests
- `POST /bookings/` - create booking (authenticated)
- `POST /payments/` - simulate payment
- `POST /payments/webhook/` - idempotent webhook

Database: default sqlite `dev.db` in workspace. Set `DATABASE_URL` to use Postgres.

Notes and assumptions:
- Simple JWT secret in `auth.py` (for demo only)
- Webhook idempotency is by `event_id` stored on `Payment.event_id`
