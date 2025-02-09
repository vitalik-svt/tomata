import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import functools
import asyncio

from app.settings import settings


LOG_DIR = Path(settings.app_log_folder)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("tomata")
logger.setLevel(settings.app_log_level)

log_format = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')

# file handler
file_handler = TimedRotatingFileHandler(
    LOG_DIR/"app.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    utc=True
)
file_handler.setFormatter(log_format)
file_handler.suffix = "%Y-%m-%d"
logger.addHandler(file_handler)

# stdout handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)



def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    """
    For error catching, that doesn't handles by FastAPI
    Beause FastAPI catching errors only inside of request, but if it will be background async - c'est la vie!
    """

    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncatched Error!", exc_info=(exc_type, exc_value, exc_traceback))


# adding that exception handler to sys!
sys.excepthook = log_unhandled_exception


def log_function_exceptions(func):
    """
    Decorator for logging every function
    """

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {e}", exc_info=True)
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
