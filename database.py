import os

from sqlmodel import SQLModel, create_engine


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./dev.db"
)


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)


def create_db():
    # Import models before creating tables
    from models import (
        User,
        Centre,
        DiagnosticTest,
        Booking,
        Payment
    )

    SQLModel.metadata.create_all(engine)