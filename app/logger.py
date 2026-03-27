"""Central logger configuration."""

from __future__ import annotations

import logging


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create or return a configured console logger."""

    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
