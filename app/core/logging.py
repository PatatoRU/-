from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def setup_logging(level: str = "INFO") -> None:
    Path("logs").mkdir(exist_ok=True)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(message)s", stream=sys.stdout)

    file_targets = {
        "app": "logs/application.log",
        "errors": "logs/error.log",
        "telegram": "logs/telegram.log",
    }
    for logger_name, path in file_targets.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(numeric_level)
        if not any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers):
            handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3)
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)

    logging.getLogger("errors").setLevel(logging.ERROR)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
