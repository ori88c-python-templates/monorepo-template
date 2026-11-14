# feature-flags-db

The `feature_flags` logical database: one table and its Alembic history. The physical name is `POSTGRES__FEATURE_FLAGS__DATABASE`.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Migrations](#migrations)
- [Exports](#exports)

## Belongs here

- `PostgresBase`, the SQLAlchemy registry for this database only.
- `FeatureFlagRow`, the `feature_flags` table: `tenant_id`, `name`, `value`, `updated_at`, `updated_by_user_id`. `tenant_id` and `name` are one composite primary key.
- `alembic.ini` and `alembic/`, including revision `04befa978a2d`.

## Does not belong here

- `FeatureFlagService` or any other service. Services are owned by their apps and are never a package.
- `PostgresClient`. The app opens connections with `shared_postgres` and `create_postgres_config("feature_flags")`.
- Another domain's tables. A new database is a new package.

## Migrations

`alembic/env.py` loads the DSN with `create_postgres_config("feature_flags")`. It does not read Redis settings. The engine is synchronous, uses `NullPool`, and passes `CONNECT_TIMEOUT_SECONDS` only. The version table is `alembic_version` inside that physical database.

Run upgrades from this package, not from application startup:

```text
uv run --directory python alembic -c packages/feature_flags_db/alembic.ini upgrade head
```

## Exports

Import from `feature_flags_db`:

- `FeatureFlagRow`
- `PostgresBase`
