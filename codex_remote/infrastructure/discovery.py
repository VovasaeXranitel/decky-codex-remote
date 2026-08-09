import socket
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib import request


Probe = Callable[[str, str], dict[str, str] | None]
PrefixProvider = Callable[[], list[str]]


class LanDiscovery:
    def __init__(
        self,
        prefix_provider: PrefixProvider | None = None,
        probe: Probe | None = None,
        max_workers: int = 48,
    ) -> None:
        self._prefix_provider = prefix_provider or self.local_ipv4_prefixes
        self._probe = probe or self.probe_readyz
        self._max_workers = max_workers

    def scan(self, port: str, configured_host: str = "") -> dict[str, Any]:
        normalized_port = str(port or "43871").strip()
        prefixes = self._prefix_provider()
        host = str(configured_host or "").strip()

        if not prefixes:
            return {"ok": False, "message": "LAN IPv4 address not found on Steam Deck.", "devices": []}

        candidates: list[str] = []
        if host and not host.startswith(("127.", "localhost")):
            candidates.append(host)
        for prefix in prefixes[:3]:
            candidates.extend(f"{prefix}.{index}" for index in range(1, 255))

        unique_candidates = list(dict.fromkeys(candidates))
        devices: list[dict[str, str]] = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {executor.submit(self._probe, candidate, normalized_port): candidate for candidate in unique_candidates}
            for future in as_completed(future_map):
                result = future.result()
                if result:
                    devices.append(result)
                    if len(devices) >= 12:
                        break

        return {
            "ok": bool(devices),
            "message": f"Found {len(devices)} Codex server(s)." if devices else f"No Codex server on LAN port {normalized_port}. Start Codex App Server on the PC and allow it in firewall.",
            "devices": devices,
        }

    def local_ipv4_prefixes(self) -> list[str]:
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

    def probe_readyz(self, host: str, port: str) -> dict[str, str] | None:
        url = f"http://{host}:{port}/readyz"
        try:
            with request.urlopen(url, timeout=0.35) as response:
                if response.status == 200:
                    return {"host": host, "port": port, "label": f"{host}:{port}"}
        except Exception:
            return None
        return None
