"""Unprefixed Prometheus gzip flag."""

from pathlib import Path

from shared_config import PrometheusConfig, load_prometheus_config


def test_gzip_defaults_to_off() -> None:
    """The library prefers CPU over bandwidth when the variable is unset."""
    assert PrometheusConfig().SHOULD_GZIP is False
    assert load_prometheus_config(env_file=None).SHOULD_GZIP is False


def test_gzip_reads_the_shared_variable(tmp_path: Path) -> None:
    """PROMETHEUS__SHOULD_GZIP applies to every app."""
    env_file = tmp_path / ".env"
    env_file.write_text("PROMETHEUS__SHOULD_GZIP=true\n", encoding="utf-8")
    assert load_prometheus_config(env_file=env_file).SHOULD_GZIP is True
