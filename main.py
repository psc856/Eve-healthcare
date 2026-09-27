from datetime import datetime, timezone
import random
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from database import engine, create_db
from models import User, Centre, DiagnosticTest, Booking, Payment
from auth import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
)


app = FastAPI(
    title="EVE Healthcare - Diagnostic Booking API",
    version="1.0.0",
)


# ---------------------------------------------------------
# Database startup
# ---------------------------------------------------------

@app.on_event("startup")
def startup():
    create_db()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class CentreRequest(BaseModel):
    name: str
    location: str


class TestRequest(BaseModel):
    name: str
    price: float = Field(gt=0)


class BookingRequest(BaseModel):
    test_id: int
    centre_id: int
    appointment: datetime


class PaymentRequest(BaseModel):
    booking_id: int
    force_status: str | None = None


class WebhookRequest(BaseModel):
    event_id: str
    booking_id: int
    status: str


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

@app.post("/auth/signup")
def signup(data: SignupRequest):

    with Session(engine) as session:

        existing_user = session.exec(
            select(User).where(User.email == data.email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )

        user = User(
            email=data.email,
            password=get_password_hash(data.password),
            name=data.name,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "message": "User created successfully",
            "id": user.id,
            "email": user.email,
        }


@app.post("/auth/login")
def login(data: LoginRequest):

    with Session(engine) as session:

        user = session.exec(
            select(User).where(User.email == data.username)
        ).first()

        if not user or not verify_password(
            data.password,
            user.password,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        token = create_access_token(
            {
                "sub": str(user.id)
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }


# ---------------------------------------------------------
# Diagnostic Centres
# ---------------------------------------------------------

@app.post("/centres/")
def create_centre(
    data: CentreRequest,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        centre = Centre(
            name=data.name,
            location=data.location,
        )

        session.add(centre)
        session.commit()
        session.refresh(centre)

        return centre


@app.get("/centres/")
def get_centres(
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        centres = session.exec(
            select(Centre)
        ).all()

        return centres


@app.get("/centres/{centre_id}")
def get_centre(
    centre_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        centre = session.get(
            Centre,
            centre_id,
        )

        if not centre:
            raise HTTPException(
                status_code=404,
                detail="Centre not found",
            )

        return centre


# ---------------------------------------------------------
# Diagnostic Tests
# ---------------------------------------------------------

@app.post("/centres/{centre_id}/tests")
def create_test(
    centre_id: int,
    data: TestRequest,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        centre = session.get(
            Centre,
            centre_id,
        )

        if not centre:
            raise HTTPException(
                status_code=404,
                detail="Centre not found",
            )

        diagnostic_test = DiagnosticTest(
            name=data.name,
            price=data.price,
            centre_id=centre_id,
        )

        session.add(diagnostic_test)
        session.commit()
        session.refresh(diagnostic_test)

        return diagnostic_test


@app.get("/tests/")
def get_tests(
    centre_id: int | None = None,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        query = select(DiagnosticTest)

        if centre_id is not None:
            query = query.where(
                DiagnosticTest.centre_id == centre_id
            )

        tests = session.exec(query).all()

        return tests


# ---------------------------------------------------------
# Bookings
# ---------------------------------------------------------

@app.post("/bookings/")
def create_booking(
    data: BookingRequest,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        # Check test
        test = session.get(
            DiagnosticTest,
            data.test_id,
        )

        if not test:
            raise HTTPException(
                status_code=404,
                detail="Test not found",
            )

        # Check centre
        centre = session.get(
            Centre,
            data.centre_id,
        )

        if not centre:
            raise HTTPException(
                status_code=404,
                detail="Centre not found",
            )

        # Make sure the test belongs to this centre
        if test.centre_id != centre.id:
            raise HTTPException(
                status_code=400,
                detail="Test is not available at this centre",
            )

        # -------------------------------------------------
        # IMPORTANT:
        # Compare timezone-aware datetimes
        # -------------------------------------------------

        if data.appointment <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Appointment must be in the future",
            )

        booking = Booking(
            user_id=current_user.id,
            test_id=test.id,
            centre_id=centre.id,
            appointment=data.appointment,
            amount=test.price,
            status="PENDING",
        )

        session.add(booking)
        session.commit()
        session.refresh(booking)

        return booking


@app.get("/bookings/")
def get_my_bookings(
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        bookings = session.exec(
            select(Booking).where(
                Booking.user_id == current_user.id
            )
        ).all()

        return bookings


@app.get("/bookings/{booking_id}")
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        booking = session.get(
            Booking,
            booking_id,
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        # User can only access their own booking
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to access this booking",
            )

        return booking


@app.delete("/bookings/{booking_id}")
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(engine) as session:

        booking = session.get(
            Booking,
            booking_id,
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to modify this booking",
            )

        if booking.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Only pending bookings can be cancelled",
            )

        booking.status = "CANCELLED"

        session.add(booking)
        session.commit()

        return {
            "message": "Booking cancelled",
            "booking_id": booking.id,
            "status": booking.status,
        }


# ---------------------------------------------------------
# Simulated Payment
# ---------------------------------------------------------

@app.post("/payments/")
def create_payment(
    data: PaymentRequest,
    current_user: User = Depends(get_current_user),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
):

    with Session(engine) as session:

        booking = session.get(
            Booking,
            data.booking_id,
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        # User can only pay for their own booking
        if booking.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not allowed to pay for this booking",
            )

        if booking.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Booking is not pending",
            )

        # -------------------------------------------------
        # Optional idempotency for payment request
        # -------------------------------------------------

        event_id = request_id or str(uuid4())

        existing_payment = session.exec(
            select(Payment).where(
                Payment.event_id == event_id
            )
        ).first()

        if existing_payment:
            return existing_payment

        # -------------------------------------------------
        # Simulate payment result
        # -------------------------------------------------

        if data.force_status:

            status = data.force_status.upper()

            if status not in ["SUCCESS", "FAILED"]:
                raise HTTPException(
                    status_code=400,
                    detail="force_status must be SUCCESS or FAILED",
                )

        else:
            status = random.choice(
                ["SUCCESS", "FAILED"]
            )

        payment = Payment(
            booking_id=booking.id,
            amount=booking.amount,
            status=status,
            event_id=event_id,
        )

        session.add(payment)

        if status == "SUCCESS":
            booking.status = "CONFIRMED"

        else:
            booking.status = "FAILED"

        session.add(booking)

        session.commit()
        session.refresh(payment)

        return payment


# ---------------------------------------------------------
# Payment Webhook
# ---------------------------------------------------------

@app.post("/payments/webhook/")
def payment_webhook(
    data: WebhookRequest,
):

    status = data.status.upper()

    if status not in ["SUCCESS", "FAILED"]:
        raise HTTPException(
            status_code=400,
            detail="Webhook status must be SUCCESS or FAILED",
        )

    with Session(engine) as session:

        # -------------------------------------------------
        # Idempotency check
        # -------------------------------------------------

        existing_payment = session.exec(
            select(Payment).where(
                Payment.event_id == data.event_id
            )
        ).first()

        if existing_payment:

            return {
                "message": "Duplicate webhook ignored",
                "status": "IGNORED",
                "payment_id": existing_payment.id,
            }

        # -------------------------------------------------
        # Find booking
        # -------------------------------------------------

        booking = session.get(
            Booking,
            data.booking_id,
        )

        if not booking:
            raise HTTPException(
                status_code=404,
                detail="Booking not found",
            )

        # -------------------------------------------------
        # Create payment
        # -------------------------------------------------

        payment = Payment(
            booking_id=booking.id,
            amount=booking.amount,
            status=status,
            event_id=data.event_id,
        )

        session.add(payment)

        # -------------------------------------------------
        # Update booking
        # -------------------------------------------------

        if status == "SUCCESS":
            booking.status = "CONFIRMED"
        else:
            booking.status = "FAILED"

        session.add(booking)

        session.commit()
        session.refresh(payment)

        return {
            "message": "Webhook processed",
            "status": status,
            "payment_id": payment.id,
            "booking_id": booking.id,
        }