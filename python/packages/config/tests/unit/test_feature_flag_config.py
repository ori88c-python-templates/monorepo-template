"""Feature-flag cache TTL. Storage of flags is not part of this package."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shared_config import FeatureFlagConfig, load_feature_flag_config


def test_cache_ttl_defaults_to_five_minutes() -> None:
    """Unset keeps a flag for 300 seconds."""
    assert FeatureFlagConfig().CACHE_TTL_SECONDS == 300
    assert load_feature_flag_config(env_file=None).CACHE_TTL_SECONDS == 300


def test_cache_ttl_below_one_second_is_rejected() -> None:
    """Zero would mean no expiry on Redis SET EX."""
    with pytest.raises(ValidationError):
        FeatureFlagConfig(CACHE_TTL_SECONDS=0)


def test_constructed_cache_ttl_round_trips() -> None:
    """An explicit TTL is stored as given."""
    assert FeatureFlagConfig(CACHE_TTL_SECONDS=12).CACHE_TTL_SECONDS == 12


def test_loader_reads_the_unprefixed_variable(tmp_path: Path) -> None:
    """FEATURE_FLAG__CACHE_TTL_SECONDS is shared by every app that uses flags."""
    env_file = tmp_path / ".env"
    env_file.write_text("FEATURE_FLAG__CACHE_TTL_SECONDS=12\n", encoding="utf-8")
    assert load_feature_flag_config(env_file=env_file).CACHE_TTL_SECONDS == 12
