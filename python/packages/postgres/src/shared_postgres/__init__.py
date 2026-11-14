"""PostgreSQL connection wrapper shared by every app that uses a database."""

from shared_postgres.postgres_client import PostgresClient

__all__ = ["PostgresClient"]
