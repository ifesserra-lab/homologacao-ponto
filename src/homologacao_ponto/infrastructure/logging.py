from __future__ import annotations

import logging
import re


SENSITIVE_PATTERNS = [
    re.compile(r"(SIGRH_PASSWORD=)[^\s]+", re.IGNORECASE),
    re.compile(r"(password['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+", re.IGNORECASE),
    re.compile(r"(cookie['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+", re.IGNORECASE),
]


def redact_sensitive(value: object) -> str:
    text = str(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub(r"\1***", text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return redact_sensitive(rendered)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("homologacao_ponto")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingFormatter("%(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(handler)
    return logger


def log_navigation_event(logger: logging.Logger, message: str, **fields: object) -> None:
    safe_fields = {key: redact_sensitive(value) for key, value in fields.items()}
    if safe_fields:
        logger.info("%s %s", redact_sensitive(message), safe_fields)
    else:
        logger.info("%s", redact_sensitive(message))
