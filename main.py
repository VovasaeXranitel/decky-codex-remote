import os
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parent))

import decky_plugin
from codex_app_client import CodexAppClient
from codex_remote.domain.defaults import DISCONNECTED_STATE
from codex_remote.domain.models import endpoint_configured, normalize_settings, proxy_config, readyz_url
from codex_remote.infrastructure.diagnostics import ConnectivityDiagnostics
from codex_remote.infrastructure.discovery import LanDiscovery
from codex_remote.infrastructure.settings_store import SettingsStore


class Plugin:
    _client = CodexAppClient()
    _discovery = LanDiscovery()
    _diagnostics = ConnectivityDiagnostics()

    async def _main(self) -> None:
        decky_plugin.logger.info("Codex Remote backend started")
        Plugin._client.configure(Plugin._read_settings(self))

    async def _unload(self) -> None:
        Plugin._client.disconnect()
        decky_plugin.logger.info("Codex Remote backend unloaded")

    async def get_settings(self) -> dict[str, Any]:
        return Plugin._read_settings(self)

    async def set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        next_settings = Plugin._settings_store(self).write(settings)
        Plugin._client.configure(next_settings)
        return next_settings

    async def get_state(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        if not endpoint_configured(settings):
            return DISCONNECTED_STATE
        Plugin._client.configure(settings)
        return Plugin._client.state()

    async def test_connection(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        token = str(settings.get("token") or "").strip()

        if not endpoint_configured(settings):
            return {"ok": False, "message": "Server endpoint is not configured."}
        if not token:
            return {"ok": False, "message": "Server token is not configured. Scan can find the PC, but Link requires a capability token."}

        url = readyz_url(settings)
        try:
            opener = self._url_opener(settings)
            with opener.open(url, timeout=3) as response:
                if response.status == 200:
                    return {"ok": True, "message": "Codex App Server is reachable. Link validates the token."}

                return {"ok": False, "message": f"Unexpected status: {response.status}"}
        except error.URLError as exc:
            return {"ok": False, "message": f"Connection failed: {exc.reason}"}
        except Exception as exc:
            return {"ok": False, "message": f"Connection failed: {exc}"}

    async def get_diagnostics(self) -> dict[str, Any]:
        return Plugin._diagnostics.run(Plugin._read_settings(self))

    async def connect(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        if not str(settings.get("token") or "").strip():
            return {"ok": False, "message": "App Server token is required. Start Codex with --ws-auth capability-token and paste the token here."}
        Plugin._client.configure(settings)
        return Plugin._client.connect()

    async def disconnect(self) -> dict[str, Any]:
        Plugin._client.disconnect()
        return {"ok": True, "message": "Disconnected."}

    async def scan_lan(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        port = str(settings.get("port") or "43871").strip()
        configured_host = str(settings.get("host") or "").strip()
        return Plugin._discovery.scan(port, configured_host)

    async def get_account(self) -> dict[str, Any]:
        Plugin._client.configure(Plugin._read_settings(self))
        return Plugin._client.account()

    async def start_chatgpt_login(self) -> dict[str, Any]:
        Plugin._client.configure(Plugin._read_settings(self))
        return Plugin._client.start_chatgpt_login()

    async def send_action(self, action: str, payload: str | None = None) -> dict[str, Any]:
        Plugin._client.configure(Plugin._read_settings(self))
        return Plugin._client.send_action(action, payload)

    async def select_thread(self, thread_id: str) -> dict[str, Any]:
        Plugin._client.configure(Plugin._read_settings(self))
        return Plugin._client.select_thread(thread_id)

    def _settings_path(self) -> Path:
        settings_dir = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR")
        if settings_dir:
            return Path(settings_dir) / "settings.json"

        return Path(decky_plugin.DECKY_PLUGIN_SETTINGS_DIR) / "settings.json"

    def _settings_store(self) -> SettingsStore:
        return SettingsStore(Plugin._settings_path(self))

    def _read_settings(self) -> dict[str, Any]:
        settings = Plugin._settings_store(self).read()
        return normalize_settings(settings)

    def _url_opener(self, settings: dict[str, Any]) -> request.OpenerDirector:
        proxy = proxy_config(settings)
        if not proxy:
            return request.build_opener()
        proxy_url = f"http://{proxy['host']}:{proxy['port']}"
        return request.build_opener(request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
