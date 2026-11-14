# FastAPI template

Blueprint for a FastAPI app in this monorepo. It is not a uv workspace member.
It speaks as the proof app `billing_api`; `scaffold_scripts/add_app.py fastapi <name>`
copies it into `python/apps/<name>` and rewrites that identity to yours.

Shared packages supply config, logging, middleware, Redis, Postgres, and Prometheus.
This tree keeps `FeatureFlagService`, the feature-flag routes, probes, and `LifecycleManager`.
The `feature_flags` table and Alembic history live in `python/packages/feature_flags_db`.

## Run

The commands below use the proof name. In an installed app they read as that app's name.
From `python/`, after `uv sync --all-packages --all-groups`:

```text
uv run --directory apps/billing_api billing-api
uv run --directory apps/billing_api pytest
```

Settings come from the repo-root `.env`. This app reads `BILLING_API__SERVER__PORT`.
Migrations:

```text
uv run --directory python alembic -c packages/feature_flags_db/alembic.ini upgrade head
```

The image builds from the `python/` directory:

```text
docker build -f apps/billing_api/Dockerfile .
```

`MONOREPO_ROOT=/app` lets the process read environment variables when the image has no `.env`.
