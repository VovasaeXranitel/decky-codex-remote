import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from codex_remote.domain.defaults import DEFAULT_SETTINGS
from codex_remote.domain.models import normalize_settings


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> dict[str, Any]:
        if not self._path.exists():
            return dict(DEFAULT_SETTINGS)

        try:
            saved = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULT_SETTINGS)

        return normalize_settings(saved)

    def write(self, settings: Mapping[str, Any]) -> dict[str, Any]:
        normalized = normalize_settings(settings)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
        return normalized
