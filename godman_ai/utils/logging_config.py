"""Logging configuration with redaction."""

import json
import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"

SENSITIVE_PATTERNS = [
    r"password=\S+",
    r"api_key=\S+",
    r"token=\S+",
    r"secret=\S+",
]


def scrub_sensitive(text: str) -> str:
    """Redact sensitive key=value patterns from log strings."""
    if not isinstance(text, str):
        return text
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = re.sub(pattern, lambda m: m.group(0).split("=")[0] + "=***", redacted, flags=re.IGNORECASE)
    return redacted


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = scrub_sensitive(record.getMessage())
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data)


class RedactingFormatter(logging.Formatter):
    """Formatter that scrubs sensitive data from messages."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = scrub_sensitive(record.getMessage())
        if record.exc_info:
            record.exc_text = scrub_sensitive(self.formatException(record.exc_info))
        return super().format(record)


def setup_logging(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    if log_dir is None:
        env_dir = os.getenv("GODMAN_LOG_DIR")
        log_dir = Path(env_dir) if env_dir else DEFAULT_LOG_DIR

    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("godman_ai")
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "godman_ai.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setLevel(logging.DEBUG)

    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = RedactingFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"godman_ai.{name}")
    if not logger.handlers:
        setup_logging()
    return logger
