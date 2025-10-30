import typing as t

import time
import logging
import logging.handlers
import functools
from collections import deque

from . import settings


def _set_logger(logger: logging.Logger) -> None:
    """Set basic configuration for logger."""
    logger.setLevel(settings.LOG_LEVEL)
    fhandler = logging.handlers.RotatingFileHandler(settings.LOG_FILE, maxBytes=1024 ** 2, backupCount=5)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)
    chanlder = logging.StreamHandler()
    chanlder.setFormatter(formatter)
    logger.addHandler(chanlder)


def timer(func: t.Callable, collector: deque[int] | None = None) -> t.Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> t.Any:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug(f"{func.__name__} finished at {end - start:.2f} seconds")
        if collector is not None:
            collector.append(int((end - start) * 1000))
        return result
    return wrapper


logger = logging.getLogger(settings.SRV_NAME)
_set_logger(logger)
