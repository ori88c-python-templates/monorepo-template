"""Probe and scrape paths are a fixed contract, not env settings."""

from shared_config import LIVEZ_ENDPOINT, METRICS_ENDPOINT, READYZ_ENDPOINT


def test_infrastructure_paths_are_the_kubelet_and_scrape_contracts() -> None:
    """A rename here would break kubelet and Prometheus without a code change."""
    assert LIVEZ_ENDPOINT == "/livez"
    assert READYZ_ENDPOINT == "/readyz"
    assert METRICS_ENDPOINT == "/metrics"
