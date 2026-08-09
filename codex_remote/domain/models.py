from collections.abc import Mapping
from typing import Any

from .defaults import DEFAULT_SETTINGS


def normalize_settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = {**DEFAULT_SETTINGS, **dict(settings or {})}
    return {
        "host": str(raw.get("host") or "").strip(),
        "port": str(raw.get("port") or "43871").strip(),
        "token": str(raw.get("token") or "").strip(),
        "autoRefresh": bool(raw.get("autoRefresh", True)),
    }
