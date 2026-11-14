"""Process entry point."""

import uvicorn

from app.config import load_app_config
from app.lifecycle import LifecycleManager


def main() -> None:
    """Load configuration, install process hooks, build the app, and serve it.

    Configuration is read first and separately so that an invalid environment fails
    here, before a single resource is constructed. The sys.excepthook and uvicorn
    bridges are process-wide, so they are installed here rather than inside
    ``create_app``. ``log_config=None`` keeps uvicorn from wiping those handlers
    with its default ``dictConfig``. ``access_log`` follows
    ``LOGGER__ENABLE_UVICORN_ACCESS_LOGS`` so uvicorn does not clear a handler we
    just attached, and so a disabled flag emits no access lines at all.
    """
    app_config = load_app_config()
    lifecycle = LifecycleManager(app_config)
    lifecycle.install_process_logging()
    app = lifecycle.create_app()

    uvicorn.run(
        app,
        host=app_config.server.HOST,
        port=app_config.server.PORT,
        log_config=None,
        access_log=app_config.logger.ENABLE_UVICORN_ACCESS_LOGS,
    )


if __name__ == "__main__":
    main()
