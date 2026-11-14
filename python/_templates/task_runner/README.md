# Task runner template

Blueprint for a task runner in this monorepo. It is not a uv workspace member.
It speaks as the proof app `github_report`; `scaffold_scripts/add_app.py task_runner <name>`
copies it into `python/apps/<name>` and rewrites that identity to yours.

Shared packages supply config, logging, the installed version, and the GitHub client.
This tree keeps `CsvReportWriter`, `TaskRunner`, and `LifecycleManager`.
The run writes a CSV and exits. It does not listen on a port.

## Run

The commands below use the proof name. In an installed app they read as that app's name.
From `python/`, after `uv sync --all-packages --all-groups`:

```text
uv run --directory apps/github_report github-report
uv run --directory apps/github_report pytest
```

Settings come from the repo-root `.env`. This app reads `GITHUB_REPORT__GITHUB__*`
and `GITHUB_REPORT__GITHUB_REPORT__OUTPUT_DIR_PATH`. It has no server port.

The image builds from the `python/` directory:

```text
docker build -f apps/github_report/Dockerfile .
```

`MONOREPO_ROOT=/app` lets the process read environment variables when the image has no `.env`.
`docker compose up` does not start this app. Run it on its own:

```text
docker compose --profile github-report run --build --rm github-report
```
