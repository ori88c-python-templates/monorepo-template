# unit

In-process tests only.

## Belongs here

Layout mirrors `src/app/`: one directory per package, then one directory per component
under test, then one file per feature.

```
config/          app_config, github_report_config (output directory only)
services/        report/csv_report_writer
lifecycle/       lifecycle_manager
task_runner/     task_runner
distribution/    installed_app_version
```

GitHub client and adapter tests live in `python/packages/github_client`.
Records are read with `read_records` from `shared_log_manager.testing`.
Configuration comes from [`../load_app_config.py`](../load_app_config.py).

## Does not belong here

A unit test never opens a socket and never calls `api.github.com`.
