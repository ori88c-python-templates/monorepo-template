# shared-distribution

The installed version of an application import.

## Table of Contents

- [Belongs here](#belongs-here)
- [Does not belong here](#does-not-belong-here)
- [Exports](#exports)

## Belongs here

- `installed_app_version(import_name)`. Wheel installs use `packages_distributions`. Editable uv installs match a `.pth` that points at `src/`.
- `pth_points_at_src`, the editable-install check.

The composition root calls `installed_app_version(APP_NAME)` and passes that string to `LogManager`.

## Does not belong here

- Logging. `LogManager` only stamps the version it is given.
- Reading `pyproject.toml` at runtime. The version comes from installed metadata.

## Exports

Import from `shared_distribution`:

- `installed_app_version`
- `pth_points_at_src`
