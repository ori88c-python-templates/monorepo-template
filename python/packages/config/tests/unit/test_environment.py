"""Deployment environment and the probe-schema flag."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared_config import Environment, load_environment


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (Environment.LOCAL, True),
        (Environment.DEV, True),
        (Environment.STAGING, False),
        (Environment.PROD, False),
    ],
)
def test_include_probes_in_schema_is_local_and_dev_only(env: Environment, expected: bool) -> None:
    """Local and dev include probe routes in the schema. Staging and prod do not."""
    assert env.include_probes_in_schema() is expected


def test_environment_defaults_to_dev_when_unset() -> None:
    """A process with no ENV variable stays on the polyrepo default."""
    assert load_environment(env_file=None) is Environment.DEV


def test_environment_reads_env_file(tmp_path: Path) -> None:
    """ENV in the chosen file selects the deployment environment."""
    env_file = tmp_path / ".env"
    env_file.write_text("ENV=local\n", encoding="utf-8")
    assert load_environment(env_file=env_file) is Environment.LOCAL


def test_process_environment_overrides_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The process environment wins so a launch script can override .env."""
    env_file = tmp_path / ".env"
    env_file.write_text("ENV=local\n", encoding="utf-8")
    monkeypatch.setenv("ENV", "prod")
    assert load_environment(env_file=env_file) is Environment.PROD


def test_unknown_environment_is_rejected(tmp_path: Path) -> None:
    """Typos fail at startup instead of falling through to dev."""
    env_file = tmp_path / ".env"
    env_file.write_text("ENV=nope\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_environment(env_file=env_file)
