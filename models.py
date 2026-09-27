from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password: str
    name: Optional[str] = None


class Centre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str

    tests: List["DiagnosticTest"] = Relationship(back_populates="centre")


class DiagnosticTest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float

    centre_id: int = Field(foreign_key="centre.id")
    centre: Optional[Centre] = Relationship(back_populates="tests")


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id")
    test_id: int = Field(foreign_key="diagnostictest.id")
    centre_id: int = Field(foreign_key="centre.id")

    appointment: datetime
    amount: float
    status: str = "PENDING"


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    booking_id: int = Field(foreign_key="booking.id")
    amount: float
    status: str

    # Used to make webhook events idempotent
    event_id: str = Field(unique=True, index=True)


class WebhookEvent(SQLModel):
    event_id: str
    booking_id: int
    status: str