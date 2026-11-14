"""Insert, rename, and remove one app's lines in ``.env.example``."""

import re
from typing import Final

from helpers.errors import ScaffoldError
from helpers.names import FASTMCP, TASK_RUNNER, AppIdentity, identifier_boundary

_PORT_LINE: Final = re.compile(r"(?m)^[A-Z][A-Z0-9_]*__SERVER__PORT=.*\n")
_MCP_LINE: Final = re.compile(r"(?m)^# [A-Z][A-Z0-9_]*__MCP__.*\n")
_TASK_RUNNER_LINE: Final = re.compile(r"(?m)^# [A-Z][A-Z0-9_]*__GITHUB.*\n")
_SERVER_HEADER: Final = "# --- Server (per app)"
_MCP_HEADER: Final = "# --- MCP (per app)"
_TASK_RUNNER_HEADER: Final = "# --- Task runner (per app)"


def add_app_env(text: str, identity: AppIdentity) -> str:
    """Add the server port, and the MCP comments for a FastMCP app.

    The new line goes after the last line of its kind. In a workspace with
    no app yet, it goes after the comment block that opens that section.

    Raises:
        ScaffoldError: The file has neither an app line nor the section
            header, or the port line is already present.
    """
    if identity.category == TASK_RUNNER:
        return _add_task_runner_env(text, identity)
    prefix = identity.env_prefix
    if re.search(rf"(?m)^{prefix}__SERVER__PORT=", text):
        message = f".env.example already defines {prefix}__SERVER__PORT."
        raise ScaffoldError(message)
    port_line = f"{prefix}__SERVER__PORT={identity.port}\n"
    text = _insert_in_section(text, _PORT_LINE, _SERVER_HEADER, port_line)
    if identity.category == FASTMCP:
        comments = f"# {prefix}__MCP__PATH=/mcp\n# {prefix}__MCP__ENABLE_SSE_STREAM_RESPONSE=true\n"
        text = _insert_in_section(text, _MCP_LINE, _MCP_HEADER, comments)
    return text


def rename_app_env(text: str, source: AppIdentity, target: AppIdentity) -> str:
    """Rename the app prefix and keep the port value."""
    pattern = re.compile(rf"{identifier_boundary()}{re.escape(source.env_prefix)}__")
    return pattern.sub(f"{target.env_prefix}__", text)


def remove_app_env(text: str, identity: AppIdentity) -> str:
    """Remove active and commented lines that belong to this app prefix."""
    pattern = re.compile(rf"(?m)^(?:# )?{re.escape(identity.env_prefix)}__.*\n")
    return pattern.sub("", text)


def _add_task_runner_env(text: str, identity: AppIdentity) -> str:
    """Insert commented GitHub and report lines. A task runner has no server port."""
    prefix = identity.env_prefix
    if re.search(rf"(?m)^# {prefix}__GITHUB", text):
        message = f".env.example already defines {prefix}__GITHUB lines."
        raise ScaffoldError(message)
    comments = (
        f"# {prefix}__GITHUB__ORG_URL=https://github.com/microsoft\n"
        f"# {prefix}__GITHUB__REPOS_LIMIT=4\n"
        f"# {prefix}__GITHUB__TOKEN=\n"
        f"# {prefix}__GITHUB__REQUEST_TIMEOUT_SECONDS=10\n"
        f"# {prefix}__GITHUB_REPORT__OUTPUT_DIR_PATH=github_reports\n"
    )
    return _insert_in_section(text, _TASK_RUNNER_LINE, _TASK_RUNNER_HEADER, comments)


def _insert_in_section(
    text: str,
    line: re.Pattern[str],
    header: str,
    insertion: str,
) -> str:
    """Insert after the last ``line`` match, or after ``header``'s comment block.

    Raises:
        ScaffoldError: Neither an existing line nor the header is present.
    """
    matches = list(line.finditer(text))
    if matches:
        end = matches[-1].end()
        return text[:end] + insertion + text[end:]
    start = text.find(header)
    if start == -1:
        message = f".env.example has no section that starts with {header!r}."
        raise ScaffoldError(message)
    end = _end_of_comment_block(text, start)
    return text[:end] + insertion + text[end:]


def _end_of_comment_block(text: str, start: int) -> int:
    """Return the offset just after the comment lines that begin at ``start``."""
    position = start
    while position < len(text):
        newline = text.find("\n", position)
        line_end = len(text) if newline == -1 else newline + 1
        if not text.startswith("#", position):
            return position
        position = line_end
    return position
