"""SQLAlchemy engine and session factory.

Reads ``DATABASE_URL`` from Settings and creates a single ``Engine``
and ``sessionmaker``.  These are imported by the dependency injector
and by health-check routines.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
