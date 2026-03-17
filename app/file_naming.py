import re
from datetime import datetime
from typing import Optional


_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def sanitize_file_component(value: Optional[str], default: str = "unknown") -> str:
    text = (value or "").strip()
    if not text:
        return default

    cleaned = _UNSAFE_CHARS.sub("-", text).strip("-_")
    return cleaned or default


def build_participant_timestamp_base(
    participant_id: Optional[str],
    dt: Optional[datetime] = None,
    fallback_id: Optional[str] = None,
) -> str:
    stamp = (dt or datetime.utcnow()).strftime("%Y%m%d_%H%M%S")
    identity = sanitize_file_component(participant_id, default="")
    if not identity:
        identity = sanitize_file_component(fallback_id, default="unknown")
    return f"{identity}_{stamp}"
