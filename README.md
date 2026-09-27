# EVE Healthcare - Demo Backend

A simple FastAPI backend for diagnostic test bookings with JWT authentication and simulated payments.

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

API documentation is available at:

`http://127.0.0.1:8000/docs`


## Main APIs

* `POST /auth/signup` - Create a user
* `POST /auth/login` - Login and get JWT token
* `POST /centres/` - Create a diagnostic centre
* `GET /centres/` - List diagnostic centres
* `POST /centres/{id}/tests` - Add a test to a centre
* `GET /tests/` - List available tests
* `POST /bookings/` - Create a booking
* `GET /bookings/` - View your bookings
* `GET /bookings/{id}` - View a booking
* `DELETE /bookings/{id}` - Cancel a booking
* `POST /payments/` - Simulate a payment
* `POST /payments/webhook/` - Receive payment updates

## Booking Flow

User signup → Login → Select centre and test → Create booking → Payment → Booking confirmed or failed.

Bookings start with `PENDING` status. Successful payments change them to `CONFIRMED`, while failed payments change them to `FAILED`.

## Database

SQLite is used by default for easy local setup. PostgreSQL can be used by setting the `DATABASE_URL` environment variable.

## Tests

Run the tests using:

```bash
pytest tests.py -v
```

The tests cover authentication, booking creation, payments, invalid bookings, and duplicate webhook events.

## Assumptions

* Payments are simulated and no real payment gateway is used.
* JWT authentication is used for protected APIs.
* Users can only access and modify their own bookings.
* Webhook events use a unique `event_id` to prevent duplicate processing.
* Basic validation and authorization checks are included.

## Future Improvements

With more time, I would add database migrations, stronger secret management, structured logging, rate limiting, and more integration tests.
