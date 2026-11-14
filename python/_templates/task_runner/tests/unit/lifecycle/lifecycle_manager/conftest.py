"""Build a real LifecycleManager that logs into the shared ``sink``."""

from io import BytesIO
from pathlib import Path

import pytest

from app.lifecycle import LifecycleManager
from tests.load_app_config import load_app_config
from tests.mock_github import mock_github


@pytest.fixture
def lifecycle_manager(sink: BytesIO, tmp_path: Path) -> LifecycleManager:
    """Provide the composition root with its log stream injected.

    ``install_process_logging`` is never called here: these tests must not replace
    process-wide hooks. The GitHub SDK is a mock transport, and the manager still
    constructs ``GithubClient`` with its own child logger. The report directory comes
    from config, pointed at ``tmp_path``, so the CSV is not written into the repository.

    Args:
        sink: Buffer that receives every record the run emits.
        tmp_path: Directory the dated CSV is written into.

    Returns:
        A manager whose ``create_task_runner`` the tests enter directly.
    """
    env_file = tmp_path / "settings.env"
    output_dir = tmp_path.as_posix()
    env_file.write_text(
        f"GITHUB_REPORT__GITHUB_REPORT__OUTPUT_DIR_PATH={output_dir}\n",
        encoding="utf-8",
    )
    return LifecycleManager(
        load_app_config(env_file),
        stream=sink,
        github=mock_github().github,
    )
