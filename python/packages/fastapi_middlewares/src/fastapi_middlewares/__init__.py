"""FastAPI-only HTTP middleware.

FastMCP apps do not depend on this package, so they do not install ``secure``.
"""

from fastapi_middlewares.secure_headers import SecureASGIMiddleware, default_secure_headers

__all__ = [
    "SecureASGIMiddleware",
    "default_secure_headers",
]
