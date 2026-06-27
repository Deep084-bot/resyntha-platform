"""Database connectivity check.

Provides ``check_database`` which is called by the ``/ready`` health
endpoint.  It executes ``SELECT 1`` and returns ``True`` on success,
``False`` on any failure.  No exceptions propagate to the caller.
"""

from sqlalchemy import text

from app.database.session import engine


def check_database() -> bool:
    """Return ``True`` if the database is reachable, ``False`` otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False
