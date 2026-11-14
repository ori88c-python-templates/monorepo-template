"""The real workspace graph selects dependents and keeps an app change local."""

from pathlib import Path

from helpers.classify_changes import select
from helpers.workspace_graph import load_graph

_PYTHON = Path(__file__).resolve().parents[2] / "python"


def test_real_workspace_follows_package_dependents() -> None:
    """``shared-config`` reaches ``github_client``.

    ``middlewares``, ``fastapi_middlewares``, and ``distribution`` do not depend
    on it, so they stay out. The shipped workspace has no app, so this test
    asserts on packages only.
    """
    graph = load_graph(_PYTHON)
    config_change = select(graph, ["python/packages/config/src/shared_config/loading.py"])
    assert "config" in config_change.packages
    assert "github_client" in config_change.packages
    assert "middlewares" not in config_change.packages
    assert "fastapi_middlewares" not in config_change.packages
    assert "distribution" not in config_change.packages


def test_an_app_file_selects_that_app_only(tmp_path: Path) -> None:
    """A change inside one app does not reach the packages it depends on."""
    _write_member(tmp_path, "packages/alpha", "alpha", ())
    _write_member(tmp_path, "apps/one", "one", ("alpha",))
    _write_member(tmp_path, "apps/two", "two", ("alpha",))
    _write_root(tmp_path, ("packages/alpha", "apps/one", "apps/two"))

    graph = load_graph(tmp_path / "python")
    app_change = select(graph, ["python/apps/one/src/one/main.py"])

    assert app_change.packages == ()
    assert app_change.apps == ("one",)


def _write_root(root: Path, members: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{member}"' for member in members)
    path = root / "python" / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"[tool.uv.workspace]\nmembers = [{listed}]\n", encoding="utf-8")


def _write_member(root: Path, member: str, name: str, dependencies: tuple[str, ...]) -> None:
    listed = ", ".join(f'"{item}"' for item in dependencies)
    path = root / "python" / member / "pyproject.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\ndependencies = [{listed}]\n',
        encoding="utf-8",
    )
