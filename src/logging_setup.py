"""Logging so failures end up in a log file instead of disappearing."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src import paths


def setup_logging() -> None:
    root = logging.getLogger("veggiequest")
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    root.addHandler(stream)
    try:
        file_handler = RotatingFileHandler(
            paths.log_file(), maxBytes=200_000, backupCount=2, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        pass  # no log file is not worth crashing for; console logging still works
