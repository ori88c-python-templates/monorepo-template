# FastMCP template

Blueprint for a FastMCP app in this monorepo. It is not a uv workspace member.
It speaks as the proof app `notes_mcp`; `scaffold_scripts/add_app.py fastmcp <name>`
copies it into `python/apps/<name>` and rewrites that identity to yours.

Shared packages supply config, logging, middleware, Redis, and Prometheus.
This tree keeps `UserNotesService`, the notes MCP primitives, probes, and `LifecycleManager`.
There is no Postgres and no secure-headers middleware.

## Run

The commands below use the proof name. In an installed app they read as that app's name.
From `python/`, after `uv sync --all-packages --all-groups`:

```text
uv run --directory apps/notes_mcp notes-mcp
uv run --directory apps/notes_mcp pytest
```

Settings come from the repo-root `.env`. This app reads `NOTES_MCP__SERVER__PORT`.

The image builds from the `python/` directory:

```text
docker build -f apps/notes_mcp/Dockerfile .
```

`MONOREPO_ROOT=/app` lets the process read environment variables when the image has no `.env`.
