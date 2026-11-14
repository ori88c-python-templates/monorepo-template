"""Immutable identity constants that must not be overridden by the environment.

The log ``app`` identity is a contract with observability: dashboards and alerts filter
on it. It is not a deployment setting.
"""

from typing import Final

APP_NAME: Final = "github_report"
