# -*- coding: utf-8 -*-
import logging
import subprocess
from typing import List

from simple_log_factory.log_factory import log_factory

_logger: logging = None


def get_logger() -> logging:
    global _logger
    if _logger is None:
        _logger = log_factory("git alias", unique_handler_types=True)
    return _logger


def run_external_command(command: List[str]) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.replace("[0m", "").replace("", "").strip()
        return output
    except FileNotFoundError:
        raise Exception("Azure CLI (az) command not found.")
