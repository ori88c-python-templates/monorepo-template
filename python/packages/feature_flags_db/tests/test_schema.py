"""The feature_flags table is the only schema in this package."""

from feature_flags_db import FeatureFlagRow, PostgresBase
from feature_flags_db.constants import LOGICAL_KEY


def test_feature_flags_table_has_the_composite_primary_key() -> None:
    """tenant_id and name identify one flag. The service is not in this package."""
    table = PostgresBase.metadata.tables["feature_flags"]
    assert table is FeatureFlagRow.__table__
    assert [column.name for column in table.primary_key.columns] == ["tenant_id", "name"]
    assert {column.name for column in table.columns} == {
        "tenant_id",
        "name",
        "value",
        "updated_at",
        "updated_by_user_id",
    }


def test_alembic_logical_key_is_feature_flags() -> None:
    """env.py loads POSTGRES__FEATURE_FLAGS__DATABASE, not a bare POSTGRES__DATABASE."""
    assert LOGICAL_KEY == "feature_flags"
