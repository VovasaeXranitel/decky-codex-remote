from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse, urlunparse

from .defaults import DEFAULT_SETTINGS


def normalize_settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    raw = {**DEFAULT_SETTINGS, **dict(settings or {})}
    return {
        "host": str(raw.get("host") or "").strip(),
        "port": str(raw.get("port") or "43871").strip(),
        "serverUrl": str(raw.get("serverUrl") or "").strip(),
        "token": str(raw.get("token") or "").strip(),
        "autoRefresh": bool(raw.get("autoRefresh", True)),
        "proxyEnabled": bool(raw.get("proxyEnabled", False)),
        "proxyHost": str(raw.get("proxyHost") or "127.0.0.1").strip(),
        "proxyPort": str(raw.get("proxyPort") or "12334").strip(),
    }


def endpoint_configured(settings: Mapping[str, Any]) -> bool:
    normalized = normalize_settings(settings)
    return bool(normalized["serverUrl"] or (normalized["host"] and normalized["port"]))


def readyz_url(settings: Mapping[str, Any]) -> str:
    normalized = normalize_settings(settings)
    server_url = normalized["serverUrl"]
    if not server_url:
        return f"http://{normalized['host']}:{normalized['port']}/readyz"
    parsed = urlparse(server_url)
    scheme = "https" if parsed.scheme == "wss" else "http"
    return urlunparse((scheme, parsed.netloc, "/readyz", "", "", ""))


def proxy_config(settings: Mapping[str, Any]) -> dict[str, str] | None:
    normalized = normalize_settings(settings)
    if not normalized["proxyEnabled"]:
        return None
    return {
        "host": normalized["proxyHost"],
        "port": normalized["proxyPort"],
    }
