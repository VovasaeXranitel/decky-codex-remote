import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any

from codex_remote.domain.models import endpoint_configured, normalize_settings, proxy_config


Check = dict[str, str]


class ConnectivityDiagnostics:
    def __init__(
        self,
        proxy_probe: Callable[[str, str], bool] | None = None,
        vpn_probe: Callable[[], bool] | None = None,
    ) -> None:
        self._proxy_probe = proxy_probe or self._probe_proxy
        self._vpn_probe = vpn_probe or self._probe_vpn

    def run(self, settings: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_settings(settings)
        checks = [
            self._endpoint_check(normalized),
            self._token_check(normalized),
            self._proxy_check(normalized),
            self._vpn_check(normalized),
        ]
        return {
            "ok": all(check["status"] in {"ok", "skipped"} for check in checks),
            "checks": checks,
        }

    def _endpoint_check(self, settings: dict[str, Any]) -> Check:
        if endpoint_configured(settings):
            endpoint = settings["serverUrl"] or f"{settings['host']}:{settings['port']}"
            return {"id": "endpoint", "label": "Endpoint", "status": "ok", "message": endpoint}
        return {"id": "endpoint", "label": "Endpoint", "status": "failed", "message": "Configure LAN host/port or Server URL."}

    def _token_check(self, settings: dict[str, Any]) -> Check:
        if settings["token"]:
            return {"id": "token", "label": "Token", "status": "ok", "message": "Capability token is set."}
        return {"id": "token", "label": "Token", "status": "failed", "message": "Paste the App Server capability token."}

    def _proxy_check(self, settings: dict[str, Any]) -> Check:
        proxy = proxy_config(settings)
        if not proxy:
            return {"id": "proxy", "label": "Proxy", "status": "skipped", "message": "Proxy mode is off."}
        ok = self._proxy_probe(proxy["host"], proxy["port"])
        if ok:
            return {"id": "proxy", "label": "Proxy", "status": "ok", "message": f"{proxy['host']}:{proxy['port']} is reachable."}
        return {"id": "proxy", "label": "Proxy", "status": "failed", "message": f"{proxy['host']}:{proxy['port']} is not reachable."}

    def _vpn_check(self, settings: dict[str, Any]) -> Check:
        if not settings["proxyEnabled"]:
            return {"id": "vpn", "label": "VPN", "status": "skipped", "message": "VPN is optional for LAN mode."}
        if self._vpn_probe():
            return {"id": "vpn", "label": "VPN", "status": "ok", "message": "Tunnel interface is up."}
        return {"id": "vpn", "label": "VPN", "status": "warning", "message": "Proxy may work, but no tun interface was detected."}

    def _probe_proxy(self, host: str, port: str) -> bool:
        try:
            with socket.create_connection((host, int(port)), timeout=2):
                return True
        except Exception:
            return False

    def _probe_vpn(self) -> bool:
        return Path("/sys/class/net/tun0").exists()
