"""Declarative base for the feature_flags database."""

from sqlalchemy.orm import DeclarativeBase


class PostgresBase(DeclarativeBase):
    """SQLAlchemy registry for this database only.

    Another logical database gets its own base in its own package. Production
    never calls ``create_all``. Schema changes are ``alembic upgrade head``
    from this package, not from an application process.
    """
