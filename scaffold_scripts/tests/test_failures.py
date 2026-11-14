"""Commands stop before they write when the app name is wrong."""

from pathlib import Path

import pytest

from add_app import main as add_main
from delete_app import main as delete_main
from helpers.errors import ScaffoldError
from helpers.operations import add_app, delete_app, rename_app
from rename_app import main as rename_main
from support import bare_repo


def _refuse(python_dir: Path) -> None:
    """Fail when a rejected command still refreshes the lock."""
    message = f"sync should not run in {python_dir}"
    raise AssertionError(message)


def test_add_rejects_a_duplicate_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A second app with the same directory name is refused."""
    paths = bare_repo(tmp_path)
    paths.app_dir("orders_api").mkdir()

    with pytest.raises(SystemExit) as caught:
        add_main(["fastapi", "orders_api"], paths=paths, sync=_refuse)

    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert error == "App 'orders_api' already exists at python/apps/orders_api.\n"


def test_add_rejects_an_invalid_name(tmp_path: Path) -> None:
    """Hyphens cannot be env prefixes."""
    with pytest.raises(ScaffoldError, match="app name"):
        add_app(bare_repo(tmp_path), "fastapi", "orders-api", sync=_refuse)


def test_rename_rejects_a_missing_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rename does not create the target when the source is absent."""
    with pytest.raises(SystemExit) as caught:
        rename_main(["missing_api", "other_api"], paths=bare_repo(tmp_path), sync=_refuse)

    assert caught.value.code == 1
    assert capsys.readouterr().err == "App 'missing_api' does not exist.\n"


def test_rename_rejects_an_existing_target(tmp_path: Path) -> None:
    """Rename stops when the target directory is already there."""
    paths = bare_repo(tmp_path)
    paths.app_dir("orders_api").mkdir()
    paths.app_dir("other_api").mkdir()

    with pytest.raises(ScaffoldError, match="already exists at python/apps/other_api"):
        rename_app(paths, "orders_api", "other_api", sync=_refuse)


def test_delete_rejects_a_missing_app(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Delete does not invent an app in order to remove it."""
    with pytest.raises(SystemExit) as caught:
        delete_main(["missing_api"], paths=bare_repo(tmp_path), sync=_refuse)

    assert caught.value.code == 1
    assert capsys.readouterr().err == "App 'missing_api' does not exist.\n"


def test_delete_library_uses_the_same_missing_message(tmp_path: Path) -> None:
    """The library and the command report the same missing-app sentence."""
    with pytest.raises(ScaffoldError, match=r"App 'missing_api' does not exist\."):
        delete_app(bare_repo(tmp_path), "missing_api", sync=_refuse)
