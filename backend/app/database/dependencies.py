"""FastAPI dependency-injection helpers for database sessions.

Provides ``get_db`` — an async generator that yields a SQLAlchemy
``Session`` and ensures it is always closed after the request
completes.
"""

from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.database.session import SessionLocal


async def get_db() -> AsyncIterator[Session]:
    """Yield a database session for the request lifetime.

    Usage in a route handler::

        @router.get("/items")
        async def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
