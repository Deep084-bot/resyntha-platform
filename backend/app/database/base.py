"""SQLAlchemy declarative base for Resyntha.

Defines the ``Base`` class that every ORM model will inherit from.
Constraint-naming conventions are applied here so that Alembic
auto-generated migrations produce consistent, predictable constraint
names across all environments.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for constraints — Alembic uses these patterns when
# autogenerating migration names.
_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Abstract base for all Resyntha ORM models."""

    metadata = MetaData(naming_convention=_convention)
