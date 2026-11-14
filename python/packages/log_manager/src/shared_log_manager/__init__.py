"""Structured logging: the factory for injectable named child loggers.

The install functions mutate process-global stdlib loggers. ``LogManager`` itself
does not. A FastAPI app calls the uvicorn installers and leaves
``install_fastmcp_logging`` unused. A FastMCP app calls that installer as well.
A task runner calls ``install_stdlib_log_bridge`` and does not call the uvicorn
or FastMCP installers. None of these functions import FastAPI, FastMCP, or uvicorn.
"""

from shared_log_manager.asyncio_exception_handler import make_asyncio_exception_handler
from shared_log_manager.fastmcp_log_handler import install_fastmcp_logging
from shared_log_manager.log_manager import LogManager
from shared_log_manager.stdlib_log_bridge import install_stdlib_log_bridge
from shared_log_manager.stdlib_log_handler import StdlibLogHandler
from shared_log_manager.sys_excepthook import make_sys_excepthook
from shared_log_manager.uvicorn_access_log_handler import install_uvicorn_access_logging
from shared_log_manager.uvicorn_asgi_exception_filter import UvicornAsgiExceptionFilter
from shared_log_manager.uvicorn_error_log_handler import install_uvicorn_error_logging
from shared_log_manager.uvicorn_log_handler import UvicornLogHandler

__all__ = [
    "LogManager",
    "StdlibLogHandler",
    "UvicornAsgiExceptionFilter",
    "UvicornLogHandler",
    "install_fastmcp_logging",
    "install_stdlib_log_bridge",
    "install_uvicorn_access_logging",
    "install_uvicorn_error_logging",
    "make_asyncio_exception_handler",
    "make_sys_excepthook",
]
