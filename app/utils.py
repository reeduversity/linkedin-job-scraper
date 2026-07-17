from __future__ import annotations

from datetime import datetime
from typing import Any


def normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)


def normalize_date(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def normalize_salary(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)


def is_valid_url(value: Any) -> bool:
    if value is None:
        return False
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    return cleaned.startswith(("http://", "https://"))
