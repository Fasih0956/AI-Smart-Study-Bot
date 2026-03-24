"""Centralized logger with color output and file logging."""

import logging
import colorlog
from pathlib import Path
from datetime import datetime


def setup_logger(name: str) -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler with colors
    console = colorlog.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s: %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }
    ))

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
