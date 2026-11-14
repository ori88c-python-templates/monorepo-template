"""Port selection, and token rewrites that survive string escapes."""

from helpers.names import AppIdentity, next_app_port, replace_identity, replace_symbol

_PROOF = AppIdentity(name="github_report", category="task_runner", port=None)
_NEW = AppIdentity(name="nightly_export", category="task_runner", port=None)


def test_next_port_skips_comments_and_stays_at_least_8081() -> None:
    """Commented ports do not count, and the first app still starts at 8081."""
    assert next_app_port("") == 8081
    assert next_app_port("# BILLING_API__SERVER__PORT=9000\n") == 8081
    ports = "BILLING_API__SERVER__PORT=8081\nNOTES_MCP__SERVER__PORT=8082\n"
    assert next_app_port(ports) == 8083


def test_env_prefix_after_a_backslash_escape_is_rewritten() -> None:
    r"""``"\nGITHUB_REPORT__..."`` in a test literal is a token, not the tail of ``n``."""
    source = r'"ENV=prod\nGITHUB_REPORT__LOGGER__MIN_LOG_LEVEL=debug\n"'

    rewritten = replace_identity(source, _PROOF, _NEW)

    assert rewritten == r'"ENV=prod\nNIGHTLY_EXPORT__LOGGER__MIN_LOG_LEVEL=debug\n"'


def test_env_prefix_inside_another_identifier_is_left_alone() -> None:
    """A longer identifier that ends with the prefix is not this app's variable."""
    assert replace_identity("OTHER_GITHUB_REPORT__X=1", _PROOF, _NEW) == "OTHER_GITHUB_REPORT__X=1"


def test_symbol_after_an_escape_is_rewritten_and_a_suffix_is_not() -> None:
    """The same boundary applies to the directory and distribution names."""
    assert replace_symbol(r"a\ngithub_report b", "github_report", "x") == r"a\nx b"
    assert replace_symbol("xgithub_report", "github_report", "x") == "xgithub_report"
    assert replace_symbol("github_report_db", "github_report", "x") == "github_report_db"
