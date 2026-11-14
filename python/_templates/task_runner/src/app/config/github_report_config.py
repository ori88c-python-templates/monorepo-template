"""Where this app writes the CSV. GitHub settings live in ``github_client``."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Self

from pydantic import BaseModel, model_validator

from app.config.app_consts import APP_NAME
from shared_config import load_app_resource
from shared_config.loading import USE_ROOT_ENV, UseRootEnv

_CSV_SUFFIX: Final = ".csv"
_REPORT_FILENAME_SUFFIX: Final = "_popular_github_repos.csv"
_RESOURCE: Final = "GITHUB_REPORT"
# The variable a user has to fix, including this app's prefix.
_ENV_NAME: Final = f"{APP_NAME.upper()}__{_RESOURCE}__OUTPUT_DIR_PATH"


class GithubReportConfig(BaseModel):
    """Directory the CSV is written into.

    Attributes:
        OUTPUT_DIR_PATH: Directory the CSV is written into. The dated filename is not
            part of this setting; ``REPORT_PATH`` adds it. The directory does not have
            to exist yet.
    """

    OUTPUT_DIR_PATH: str = "github_reports"

    @model_validator(mode="after")
    def _require_output_directory(self) -> Self:
        """Reject a directory string that is not a usable path shape.

        Existence is not checked: the writer creates the directory on the first run.

        Returns:
            The validated model.

        Raises:
            ValueError: If the value is blank, contains ``.`` or ``..``, has an empty
                segment, or names a CSV file instead of a directory.
        """
        segments = self._output_dir_segments()
        if not segments:
            message = f"{_ENV_NAME} must name a directory."
            raise ValueError(message)
        if any(segment == "" for segment in segments):
            message = f"{_ENV_NAME} must not contain empty segments."
            raise ValueError(message)
        if any(segment in {".", ".."} for segment in segments):
            message = f"{_ENV_NAME} must not contain '.' or '..'."
            raise ValueError(message)
        if segments[-1].lower().endswith(_CSV_SUFFIX):
            message = (
                f"{_ENV_NAME} is a directory, not a CSV file. "
                "The dated filename is added by the application."
            )
            raise ValueError(message)
        return self

    @property
    def REPORT_PATH(self) -> Path:
        """Today's CSV path under ``OUTPUT_DIR_PATH``.

        The filename is ``YYYY_MM_DD_popular_github_repos.csv`` for the current UTC
        date. A second run on the same date therefore targets the same file.

        Returns:
            The directory from configuration plus the dated filename.
        """
        day = datetime.now(UTC).strftime("%Y_%m_%d")
        return Path(self.OUTPUT_DIR_PATH.strip()) / f"{day}{_REPORT_FILENAME_SUFFIX}"

    def _output_dir_segments(self) -> list[str]:
        """Split ``OUTPUT_DIR_PATH`` into segments.

        A trailing slash is ignored. An internal ``//`` still yields an empty segment
        so the validator can reject it. A leading slash stays out of the segment list
        only as the root marker, not a name.

        Returns:
            The directory segments, in order. Empty when the value is blank.
        """
        normalized = self.OUTPUT_DIR_PATH.strip().replace("\\", "/")
        if not normalized:
            return []
        body = normalized.rstrip("/")
        parts = body.split("/")
        if normalized.startswith("/"):
            parts = parts[1:]
        return parts


def load_github_report_config(
    app_name: str,
    *,
    env_file: Path | UseRootEnv | None = USE_ROOT_ENV,
) -> GithubReportConfig:
    """Load ``<APP>__GITHUB_REPORT__OUTPUT_DIR_PATH``.

    Args:
        app_name: App directory name, such as ``github_report``.
        env_file: File to read after the process environment. Omit it to use the
            repo-root ``.env`` when that file exists. Pass ``None`` to ignore files.

    Returns:
        The output directory. Unset means ``github_reports``.

    Raises:
        ValueError: If ``app_name`` is not a lowercase identifier, or the path
            shape is unusable.
        FileNotFoundError: If ``env_file`` cannot be resolved.
    """
    return load_app_resource(GithubReportConfig, app_name, _RESOURCE, env_file=env_file)
