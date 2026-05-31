import json
import os
import socket
from pathlib import Path
from typing import Any
from urllib import error, request
from concurrent.futures import ThreadPoolExecutor, as_completed

import decky_plugin
from codex_app_client import CodexAppClient


DEFAULT_SETTINGS = {
    "host": "",
    "port": "43871",
    "token": "",
    "autoRefresh": True,
}

DISCONNECTED_STATE = {
    "status": "disconnected",
    "thread": "Decky remote",
    "task": "Configure Codex App Server connection",
    "messages": [
        "Open settings and enter your PC host, port, and Codex App Server token.",
        "No OpenAI account data is stored by the plugin.",
    ],
}


class Plugin:
    def __init__(self) -> None:
        self._client = CodexAppClient()

    async def _main(self) -> None:
        decky_plugin.logger.info("Codex Remote backend started")
        self._client.configure(self._read_settings())

    async def _unload(self) -> None:
        self._client.disconnect()
        decky_plugin.logger.info("Codex Remote backend unloaded")

    async def get_settings(self) -> dict[str, Any]:
        return self._read_settings()

    async def set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        next_settings = {**DEFAULT_SETTINGS, **settings}
        self._settings_path().parent.mkdir(parents=True, exist_ok=True)
        self._settings_path().write_text(json.dumps(next_settings, indent=2), encoding="utf-8")
        self._client.configure(next_settings)
        return next_settings

    async def get_state(self) -> dict[str, Any]:
        settings = self._read_settings()
        if not settings.get("host"):
            return DISCONNECTED_STATE
        self._client.configure(settings)
        return self._client.state()

    async def test_connection(self) -> dict[str, Any]:
        settings = self._read_settings()
        host = str(settings.get("host") or "").strip()
        port = str(settings.get("port") or "").strip()

        if not host:
            return {"ok": False, "message": "Host is not configured."}

        url = f"http://{host}:{port}/readyz"
        try:
            with request.urlopen(url, timeout=3) as response:
                if response.status == 200:
                    return {"ok": True, "message": "Codex App Server is reachable."}

                return {"ok": False, "message": f"Unexpected status: {response.status}"}
        except error.URLError as exc:
            return {"ok": False, "message": f"Connection failed: {exc.reason}"}
        except Exception as exc:
            return {"ok": False, "message": f"Connection failed: {exc}"}

    async def connect(self) -> dict[str, Any]:
        self._client.configure(self._read_settings())
        return self._client.connect()

    async def disconnect(self) -> dict[str, Any]:
        self._client.disconnect()
        return {"ok": True, "message": "Disconnected."}

    async def scan_lan(self) -> dict[str, Any]:
        settings = self._read_settings()
        port = str(settings.get("port") or "43871").strip()
        prefixes = self._local_ipv4_prefixes()
        if not prefixes:
            return {"ok": False, "message": "No LAN IPv4 address found.", "devices": []}

        candidates = []
        for prefix in prefixes[:3]:
            candidates.extend(f"{prefix}.{index}" for index in range(1, 255))

        devices: list[dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=48) as executor:
            future_map = {executor.submit(self._probe_readyz, host, port): host for host in candidates}
            for future in as_completed(future_map):
                result = future.result()
                if result:
                    devices.append(result)
                    if len(devices) >= 12:
                        break

        return {
            "ok": bool(devices),
            "message": f"Found {len(devices)} Codex server(s)." if devices else "No Codex App Server found on LAN.",
            "devices": devices,
        }

    async def get_account(self) -> dict[str, Any]:
        self._client.configure(self._read_settings())
        return self._client.account()

    async def start_chatgpt_login(self) -> dict[str, Any]:
        self._client.configure(self._read_settings())
        return self._client.start_chatgpt_login()

    async def send_action(self, action: str, payload: str | None = None) -> dict[str, Any]:
        self._client.configure(self._read_settings())
        return self._client.send_action(action, payload)

    def _local_ipv4_prefixes(self) -> list[str]:
        prefixes = set()
        try:
            hostname = socket.gethostname()
            for item in socket.getaddrinfo(hostname, None, socket.AF_INET):
                address = item[4][0]
                if address.startswith(("127.", "169.254.")):
                    continue
                parts = address.split(".")
                if len(parts) == 4:
                    prefixes.add(".".join(parts[:3]))
        except OSError:
            pass

        return sorted(prefixes)

    def _probe_readyz(self, host: str, port: str) -> dict[str, str] | None:
        url = f"http://{host}:{port}/readyz"
        try:
            with request.urlopen(url, timeout=0.35) as response:
                if response.status == 200:
                    return {"host": host, "port": port, "label": f"{host}:{port}"}
        except Exception:
            return None
        return None

    def _settings_path(self) -> Path:
        settings_dir = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR")
        if settings_dir:
            return Path(settings_dir) / "settings.json"

        return Path(decky_plugin.DECKY_PLUGIN_SETTINGS_DIR) / "settings.json"

    def _read_settings(self) -> dict[str, Any]:
        path = self._settings_path()
        if not path.exists():
            return DEFAULT_SETTINGS

        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            return {**DEFAULT_SETTINGS, **saved}
        except Exception as error:
            decky_plugin.logger.warning("Failed to read settings: %s", error)
            return DEFAULT_SETTINGS
