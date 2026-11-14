---
name: alembic
description: >-
  Add or change a logical database, its Alembic history, or its Compose
  migrate service. Use when the user asks for a database package, a
  migration, alembic upgrade, packages/<key>_db, or a migrate service.
---

# Alembic

Models and migrations for one logical database live in `python/packages/<logical_key>_db`. The key matches `^[a-z][a-z0-9_]*$`. It is not the physical database name. `create_postgres_config("<logical_key>")` reads `POSTGRES__<KEY>__DATABASE`. A missing key fails. The physical name does not default to the key. A bare `POSTGRES__DATABASE` fails. Two apps that pass the same key share that database. One process may call the function twice.

The reference package is `python/packages/feature_flags_db`. Its key is `feature_flags`. `alembic/env.py` calls `create_postgres_config("feature_flags")`.

## Package

`add_package.py` creates the empty package only. It does not write Alembic, `.env.example`, or `compose.yaml`.

The package holds the ORM models and the migration history from the start, including a database with one consumer. Apps never import apps. `shared_postgres` is the connection only.

`alembic/env.py` is not an application. It builds a synchronous engine with `NullPool`. It passes `CONNECT_TIMEOUT_SECONDS` only. It does not apply `STATEMENT_TIMEOUT_MS`. It does not construct `PostgresClient` and does not require Redis settings. The `sqlalchemy.url` in `alembic.ini` is a placeholder. The environment supplies the DSN.

One migration history and one `alembic_version` table per physical database.

Uncomment or add `POSTGRES__<KEY>__DATABASE` in `.env.example` in the same change. Commented inventory lines stay commented until that package exists.

## Migrate service

Nothing runs Alembic from an app process.

Compose has one migrate service per logical database. Add one only when an app uses a database that does not have one yet. Remove it only when no remaining app uses that database. Leave Redis, Postgres, and unrelated migrate services.

The command is:

```text
alembic -c packages/<logical_key>_db/alembic.ini upgrade head
```

The image must contain that `alembic.ini` and the `alembic/` tree. The `COPY` lines for that live in the Dockerfile the migrate service builds. The pattern is `python/_templates/fastapi/Dockerfile`:

```text
COPY packages/<logical_key>_db/alembic.ini /app/packages/<logical_key>_db/alembic.ini
COPY packages/<logical_key>_db/alembic /app/packages/<logical_key>_db/alembic
```

Those copies happen in the runtime stage. `python/.dockerignore` must not exclude them. An app that uses the database sets `POSTGRES__HOST=postgres` and waits until that migrate service has completed.
