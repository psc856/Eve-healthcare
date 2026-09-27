from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password: str
    name: Optional[str] = None


class Centre(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str
    tests: List['DiagnosticTest'] = Relationship(back_populates='centre')


class DiagnosticTest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    centre_id: Optional[int] = Field(default=None, foreign_key='centre.id')
    centre: Optional[Centre] = Relationship(back_populates='tests')


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    test_id: int
    centre_id: int
    appointment: datetime
    amount: float = 0.0
    status: str = 'PENDING'


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int
    amount: float
    status: str
    event_id: Optional[str] = None


class WebhookEvent(SQLModel):
    event_id: str
    booking_id: int
    status: str
