# -*- coding: utf-8 -*-
from functools import wraps
from raccoon_simple_stopwatch.stopwatch import StopWatch

from core.utils import get_logger


def stop_watch(message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            sw = StopWatch(True)
            logger.info(f"{message}... started!")

            result = func(*args, **kwargs)

            elapsed_time = sw.end()
            logger.info(f"{message}... done! [{elapsed_time}]")
            return result
        return wrapper
    return decorator
