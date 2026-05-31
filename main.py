import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import error, request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    "threadId": "",
    "threads": [],
    "task": "Configure Codex App Server connection",
    "transcript": [
        {
            "id": "setup",
            "kind": "system",
            "title": "Setup",
            "body": "Open settings and enter your PC host, port, and Codex App Server token.",
            "status": "",
        }
    ],
    "messages": [
        "Open settings and enter your PC host, port, and Codex App Server token.",
        "No OpenAI account data is stored by the plugin.",
    ],
}


class Plugin:
    _client = CodexAppClient()

    async def _main(self) -> None:
        decky_plugin.logger.info("Codex Remote backend started")
        Plugin._client.configure(Plugin._read_settings(self))

    async def _unload(self) -> None:
        Plugin._client.disconnect()
        decky_plugin.logger.info("Codex Remote backend unloaded")

    async def get_settings(self) -> dict[str, Any]:
        return Plugin._read_settings(self)

    async def set_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        next_settings = {**DEFAULT_SETTINGS, **settings}
        settings_path = Plugin._settings_path(self)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(next_settings, indent=2), encoding="utf-8")
        Plugin._client.configure(next_settings)
        return next_settings

    async def get_state(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        if not settings.get("host"):
            return DISCONNECTED_STATE
        Plugin._client.configure(settings)
        return Plugin._client.state()

    async def test_connection(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
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
        Plugin._client.configure(Plugin._read_settings(self))
        return Plugin._client.connect()

    async def disconnect(self) -> dict[str, Any]:
        Plugin._client.disconnect()
        return {"ok": True, "message": "Disconnected."}

    async def scan_lan(self) -> dict[str, Any]:
        settings = Plugin._read_settings(self)
        port = str(settings.get("port") or "43871").strip()
        prefixes = Plugin._local_ipv4_prefixes(self)
        configured_host = str(settings.get("host") or "").strip()

        if not prefixes:
            return {"ok": False, "message": "LAN IPv4 address not found on Steam Deck.", "devices": []}

        candidates = []
        if configured_host and not configured_host.startswith(("127.", "localhost")):
            candidates.append(configured_host)
        for prefix in prefixes[:3]:
            candidates.extend(f"{prefix}.{index}" for index in range(1, 255))

        unique_candidates = list(dict.fromkeys(candidates))

        devices: list[dict[str, str]] = []
        with ThreadPoolExecutor(max_workers=48) as executor:
            future_map = {executor.submit(Plugin._probe_readyz, self, host, port): host for host in unique_candidates}
            for future in as_completed(future_map):
                result = future.result()
                if result:
                    devices.append(result)
                    if len(devices) >= 12:
                        break

        return {
            "ok": bool(devices),
            "message": f"Found {len(devices)} Codex server(s)." if devices else f"No Codex server on LAN port {port}. Start Codex App Server on the PC and allow it in firewall.",
            "devices": devices,
        }

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

        for address in self._linux_ipv4_addresses():
            parts = address.split(".")
            if len(parts) == 4 and not address.startswith(("127.", "169.254.")):
                prefixes.add(".".join(parts[:3]))

        return sorted(prefixes)

    def _linux_ipv4_addresses(self) -> list[str]:
        addresses: list[str] = []
        commands = [
            ["ip", "-4", "route", "show", "default"],
            ["ip", "-4", "route", "show", "scope", "link"],
            ["ip", "-4", "addr", "show"],
        ]
        for command in commands:
            try:
                output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=2)
            except Exception:
                continue
            for line in output.splitlines():
                parts = line.replace("/", " ").split()
                for index, part in enumerate(parts):
                    if part == "src" and index + 1 < len(parts):
                        addresses.append(parts[index + 1])
                    elif part == "inet" and index + 1 < len(parts):
                        addresses.append(parts[index + 1])
        return addresses

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
        path = Plugin._settings_path(self)
        if not path.exists():
            return DEFAULT_SETTINGS

        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            return {**DEFAULT_SETTINGS, **saved}
        except Exception as error:
            decky_plugin.logger.warning("Failed to read settings: %s", error)
            return DEFAULT_SETTINGS
