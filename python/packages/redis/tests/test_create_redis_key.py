"""Length prefixes keep a colon inside a part from merging with the next one."""

import pytest

from shared_redis import create_redis_key


def test_length_prefixes_keep_colon_split_callers_apart() -> None:
    """Tenant ``a`` / name ``b:c`` is a different key from tenant ``a:b`` / name ``c``."""
    first = create_redis_key("billing_api", "feature_flag", "a", "b:c")
    second = create_redis_key("billing_api", "feature_flag", "a:b", "c")

    assert first == "billing_api:12:feature_flag:1:a:3:b:c"
    assert second == "billing_api:12:feature_flag:3:a:b:1:c"
    assert first != second


def test_prefix_and_parts_are_required() -> None:
    """An empty prefix or no parts is not a key."""
    with pytest.raises(ValueError, match="prefix"):
        create_redis_key("", "feature_flag")
    with pytest.raises(ValueError, match="part"):
        create_redis_key("billing_api")
