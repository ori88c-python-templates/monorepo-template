"""``from app.main import main`` writes the CSV report and exits 0."""

import csv
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def test_run_writes_the_popular_repos_csv_and_exits_zero(tmp_path: Path) -> None:
    """The subprocess reads the repo-root env file, then the variables set here.

    Args:
        tmp_path: Directory the CSV is written into. The path is absolute so the
            process working directory does not choose the file.
    """
    output_dir = tmp_path / "github_reports"
    env = {
        **os.environ,
        "GITHUB_REPORT__GITHUB__REPOS_LIMIT": "3",
        "GITHUB_REPORT__LOGGER__MIN_LOG_LEVEL": "info",
        "GITHUB_REPORT__GITHUB_REPORT__OUTPUT_DIR_PATH": output_dir.as_posix(),
    }
    token = os.environ.get("GITHUB_REPORT__GITHUB__TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        env["GITHUB_REPORT__GITHUB__TOKEN"] = token

    result = subprocess.run(
        [sys.executable, "-c", "from app.main import main; main()"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "lifecycle.task_runner.creating" in result.stdout
    assert "csv_report.written" in result.stdout
    assert "task_runner.run.completed" in result.stdout

    filename = f"{datetime.now(UTC):%Y_%m_%d}_popular_github_repos.csv"
    path = output_dir / filename
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    assert rows[0] == ["rank", "name", "stars", "forks", "language"]
    data = rows[1:]
    assert [row[0] for row in data] == ["1", "2", "3"]
    stars = [int(row[2]) for row in data]
    assert stars == sorted(stars, reverse=True)
    assert all(row[1] for row in data)
