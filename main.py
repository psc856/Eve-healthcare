from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import datetime, timezone
from typing import Optional
import random

from database import engine, create_db
from models import User, Centre, DiagnosticTest, Booking, Payment, WebhookEvent
from auth import get_password_hash, verify_password, create_access_token, get_current_user

app = FastAPI(title="EVE Healthcare - Demo")


@app.on_event("startup")
def on_startup():
    create_db()


@app.post('/auth/signup')
def signup(user: User):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == user.email)).first()
        if existing:
            raise HTTPException(400, "Email already registered")
        user.password = get_password_hash(user.password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post('/auth/login')
def login(form_data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == form_data.username)).first()
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(401, "Invalid credentials")
        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}


@app.post('/centres/')
def create_centre(centre: Centre):
    with Session(engine) as session:
        session.add(centre)
        session.commit()
        session.refresh(centre)
        return centre


@app.get('/centres/')
def list_centres():
    with Session(engine) as session:
        centres = session.exec(select(Centre)).all()
        return centres


@app.post('/centres/{centre_id}/tests')
def add_test(centre_id: int, test: DiagnosticTest):
    with Session(engine) as session:
        centre = session.get(Centre, centre_id)
        if not centre:
            raise HTTPException(404, "Centre not found")
        test.centre_id = centre_id
        session.add(test)
        session.commit()
        session.refresh(test)
        return test


@app.get('/tests/')
def list_tests(centre_id: Optional[int] = None):
    with Session(engine) as session:
        q = select(DiagnosticTest)
        if centre_id:
            q = q.where(DiagnosticTest.centre_id == centre_id)
        return session.exec(q).all()


@app.post('/bookings/')
def create_booking(booking: Booking, user=Depends(get_current_user)):
    with Session(engine) as session:
        test = session.get(DiagnosticTest, booking.test_id)
        if not test:
            raise HTTPException(404, "Test not found")
        # Coerce appointment to datetime if provided as string
        if isinstance(booking.appointment, str):
            try:
                booking.appointment = datetime.fromisoformat(booking.appointment)
            except Exception:
                raise HTTPException(400, "Invalid appointment datetime format")
        # Ensure timezone-aware datetime (SQLModel DateTime requires tz)
        if isinstance(booking.appointment, datetime) and booking.appointment.tzinfo is None:
            booking.appointment = booking.appointment.replace(tzinfo=timezone.utc)

        booking.user_id = user.id
        booking.amount = test.price
        booking.status = "PENDING"
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking


@app.post('/payments/')
def simulate_payment(booking_id: int, force_status: Optional[str] = None, x_request_id: Optional[str] = Header(None)):
    with Session(engine) as session:
        booking = session.get(Booking, booking_id)
        if not booking:
            raise HTTPException(404, "Booking not found")
        # Simulate processing
        status = force_status if force_status in ("SUCCESS", "FAILED") else random.choice(["SUCCESS", "FAILED"])
        payment = Payment(booking_id=booking_id, amount=booking.amount, status=status, event_id=x_request_id)
        # Update booking accordingly
        booking.status = "CONFIRMED" if status == "SUCCESS" else "FAILED"
        session.add(payment)
        session.add(booking)
        session.commit()
        session.refresh(payment)
        return {"payment_id": payment.id, "status": status}


@app.post('/payments/webhook/')
def payment_webhook(event: WebhookEvent):
    with Session(engine) as session:
        existing = session.exec(select(Payment).where(Payment.event_id == event.event_id)).first()
        if existing:
            return {"status": "ignored", "reason": "duplicate event"}
        booking = session.get(Booking, event.booking_id)
        if not booking:
            raise HTTPException(400, "Invalid booking")
        payment = Payment(booking_id=event.booking_id, amount=booking.amount, status=event.status, event_id=event.event_id)
        booking.status = "CONFIRMED" if event.status == "SUCCESS" else "FAILED"
        session.add(payment)
        session.add(booking)
        session.commit()
        return {"status": "ok"}
