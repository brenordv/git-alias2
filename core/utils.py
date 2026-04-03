import logging

from simple_log_factory.log_factory import log_factory

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = log_factory("git alias", unique_handler_types=True)
    return _logger
