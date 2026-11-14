"""``installed_app_version`` against injected catalogs, not the live install."""

from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

from fake_pth_distribution import FakePthDistribution, write_pth
from shared_distribution import installed_app_version

_IMPORT_NAME = "billing_api"


def test_wheel_mapping_uses_the_injected_version_lookup() -> None:
    """A ``packages_distributions`` hit does not scan ``.pth`` files."""
    result = installed_app_version(
        _IMPORT_NAME,
        dist_names_by_import={_IMPORT_NAME: ["billing-api"]},
        version_for=lambda name: f"{name}-9.9.9",
        dists=(),
    )

    assert result == "billing-api-9.9.9"


def test_editable_pth_uses_the_matching_dist_version(tmp_path: Path) -> None:
    """With an empty import map, a ``.pth`` that names ``src_dir`` wins."""
    src_dir = tmp_path.resolve()
    pth = write_pth(tmp_path, f"{src_dir}\n")
    dist = FakePthDistribution(
        files=["editable.pth"],
        path_by_file={"editable.pth": pth},
        version="1.2.3",
    )

    result = installed_app_version(
        _IMPORT_NAME,
        dist_names_by_import={},
        dists=[dist],
        src_dir=src_dir,
    )

    assert result == "1.2.3"


def test_empty_catalogs_raise_package_not_found() -> None:
    """No wheel mapping and no matching ``.pth`` is the same as a missing dist."""
    with pytest.raises(PackageNotFoundError):
        installed_app_version("missing_app", dist_names_by_import={}, dists=())
