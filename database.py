from sqlmodel import create_engine, SQLModel
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./dev.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})


def create_db():
    from models import User, Centre, DiagnosticTest, Booking, Payment
    SQLModel.metadata.create_all(engine)


# Ensure DB/tables exist on import so tests and startup both work reliably
create_db()
