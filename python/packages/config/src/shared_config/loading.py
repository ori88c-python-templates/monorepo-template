"""Read the repo-root env file and copy values into resource models.

Values are validated once, by the target ``BaseModel``. They are never round-tripped
through ``model_dump()``, which would replace a ``SecretStr`` with a redacted string
and then parse that redaction back into the model.
"""

import os
import re
from pathlib import Path
from typing import Final

from pydantic import BaseModel

from shared_config.names import validate_app_name

_RESOURCE_NAME: Final = re.compile(r"^[A-Z][A-Z0-9_]*$")

_ENV_FILE_NAME = ".env"


class UseRootEnv:
    """Sentinel: discover the repo-root ``.env`` instead of taking a caller path."""


USE_ROOT_ENV = UseRootEnv()


def repo_root() -> Path:
    """Return the monorepo root.

    ``MONOREPO_ROOT`` wins when it is set to a non-empty value. Otherwise the root
    is the nearest parent of this package that contains both ``python/pyproject.toml``
    and ``README.md``.

    Returns:
        Absolute path of the repository root.

    Raises:
        FileNotFoundError: If ``MONOREPO_ROOT`` is unset and no parent directory has
            both markers.
    """
    override = os.environ.get("MONOREPO_ROOT")
    if override:
        return Path(override).resolve()
    return _find_root(Path(__file__).resolve())


def _find_root(start: Path) -> Path:
    """Walk parents of ``start`` for the monorepo markers.

    Args:
        start: File or directory inside the tree being searched.

    Returns:
        The directory that contains both markers.

    Raises:
        FileNotFoundError: If the walk reaches the filesystem root without a match.
    """
    for parent in start.parents:
        has_workspace = (parent / "python" / "pyproject.toml").is_file()
        has_readme = (parent / "README.md").is_file()
        if has_workspace and has_readme:
            return parent
    message = (
        f"Cannot find the monorepo root from {start}. Set MONOREPO_ROOT or keep "
        "python/pyproject.toml and README.md at the repository root."
    )
    raise FileNotFoundError(message)


def resolve_env_file(env_file: Path | UseRootEnv | None) -> Path | None:
    """Resolve a loader's ``env_file`` argument to a file or to process env only.

    Args:
        env_file: The sentinel to discover the repo-root file, ``None`` to skip files,
            or a path the caller chose.

    Returns:
        The file to parse, or ``None`` when only the process environment applies.
        A missing repo-root ``.env`` is ``None`` rather than an error.

    Raises:
        FileNotFoundError: If the caller passed a path and that path is not a file,
            or if root discovery fails while using the sentinel.
    """
    if isinstance(env_file, UseRootEnv):
        candidate = repo_root() / _ENV_FILE_NAME
        if candidate.is_file():
            return candidate
        return None
    if env_file is None:
        return None
    if not env_file.is_file():
        message = f"Env file does not exist: {env_file}"
        raise FileNotFoundError(message)
    return env_file


def merged_environ(env_file: Path | None) -> dict[str, str]:
    """Merge an env file with the process environment.

    Keys are uppercased. The process environment overwrites the file. An explicit
    empty value in the process environment still wins over the file.

    Args:
        env_file: File to read, or ``None`` to use only ``os.environ``.

    Returns:
        Uppercase names mapped to their values.
    """
    env_value_by_key: dict[str, str] = {}
    if env_file is not None:
        env_value_by_key.update(_parse_env_file(env_file))
    for key, value in os.environ.items():
        env_value_by_key[key.upper()] = value
    return env_value_by_key


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv-style file.

    Full-line comments and blank lines are skipped. ``export `` is optional.
    A value wrapped in matching single or double quotes loses those quotes.
    Inline comments are kept, so a password may contain ``#``.

    Args:
        path: Existing env file.

    Returns:
        Uppercase names mapped to their values. A later line overwrites an earlier one.
    """
    env_value_by_key: dict[str, str] = {}
    env_file_lines = path.read_text(encoding="utf-8").splitlines()
    for raw_line in env_file_lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key = key.strip().upper()
        value = value.strip()
        opening = value[:1]
        if opening in {'"', "'"} and opening != value and value.endswith(opening):
            value = value[1:-1]
        if key:
            env_value_by_key[key] = value
    return env_value_by_key


def fields_from_env(
    model: type[BaseModel],
    *,
    env_prefix: str,
    env_file: Path | None,
    exclude: frozenset[str],
) -> dict[str, str]:
    """Collect raw strings for ``model`` fields that are present in the environment.

    Args:
        model: Resource model whose field names are the env leaves.
        env_prefix: Uppercase-insensitive prefix, including the trailing ``__`` when
            the leaf is nested. An empty prefix matches field names exactly.
        env_file: Already resolved file, or ``None``.
        exclude: Field names that must not be filled from this prefix. Used so
            ``POSTGRES__DATABASE`` is not treated as ``PostgresConfig.DATABASE``.

    Returns:
        Field name to raw string, for fields that were set. Omitted fields keep
        their model defaults.
    """
    env_value_by_key = merged_environ(env_file)
    prefix = env_prefix.upper()
    field_name_by_upper = {name.upper(): name for name in model.model_fields if name not in exclude}
    raw_value_by_field: dict[str, str] = {}
    for key, value in env_value_by_key.items():
        if not key.startswith(prefix):
            continue
        field_name = field_name_by_upper.get(key.removeprefix(prefix))
        if field_name is not None:
            raw_value_by_field[field_name] = value
    return raw_value_by_field


def load_model[T: BaseModel](
    model: type[T],
    *,
    env_prefix: str,
    env_file: Path | UseRootEnv | None,
    exclude: frozenset[str] = frozenset(),
) -> T:
    """Validate ``model`` from the environment.

    Args:
        model: Resource model to construct.
        env_prefix: See ``fields_from_env``.
        env_file: Loader argument, resolved here.
        exclude: Field names skipped while reading this prefix.

    Returns:
        The validated model.

    Raises:
        ValidationError: If a required field is missing or a value is invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    resolved = resolve_env_file(env_file)
    raw = fields_from_env(model, env_prefix=env_prefix, env_file=resolved, exclude=exclude)
    return model.model_validate(raw)


def load_app_resource[T: BaseModel](
    model: type[T],
    app_name: str,
    resource: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> T:
    """Validate an app-owned model from ``<APP>__<RESOURCE>__*``.

    Named loaders such as :func:`shared_config.logger_config.create_logger_config`
    stay the API for shared resources. An app calls this for a model that lives
    in that app or in a client package, so the env file rules are not copied.

    Args:
        model: Resource model whose field names are the env leaves.
        app_name: App directory name, such as ``github_report``.
        resource: Uppercase segment between the app prefix and the field, such
            as ``GITHUB``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        The validated model. Unset fields keep their defaults.

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier, or if
            ``resource`` is not an uppercase identifier.
        ValidationError: If a required field is missing or a value is invalid.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    if _RESOURCE_NAME.fullmatch(resource) is None:
        message = f"resource {resource!r} must match {_RESOURCE_NAME.pattern}"
        raise ValueError(message)
    prefix = f"{validate_app_name(app_name).upper()}__{resource}__"
    return load_model(model, env_prefix=prefix, env_file=env_file)
