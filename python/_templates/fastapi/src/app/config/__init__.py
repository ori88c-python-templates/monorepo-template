"""Application configuration: the composed model and this app's constants."""

from app.config.app_config import AppConfig, load_app_config
from app.config.app_consts import (
    APP_NAME,
    FEATURE_FLAGS_LOGICAL_KEY,
    REDOC_ENDPOINT,
    SWAGGER_DOCS_ENDPOINT,
    TENANT_ID_HEADER,
    USER_ID_HEADER,
)

__all__ = [
    "APP_NAME",
    "FEATURE_FLAGS_LOGICAL_KEY",
    "REDOC_ENDPOINT",
    "SWAGGER_DOCS_ENDPOINT",
    "TENANT_ID_HEADER",
    "USER_ID_HEADER",
    "AppConfig",
    "load_app_config",
]
