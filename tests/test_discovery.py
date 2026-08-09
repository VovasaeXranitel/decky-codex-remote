import unittest

from codex_remote.infrastructure.discovery import LanDiscovery


class LanDiscoveryTest(unittest.TestCase):
    def test_scan_probes_configured_host_first_and_deduplicates_candidates(self) -> None:
        calls: list[str] = []

        def probe(host: str, port: str) -> dict[str, str] | None:
            calls.append(host)
            if host == "192.168.1.81":
                return {"host": host, "port": port, "label": f"{host}:{port}"}
            return None

        discovery = LanDiscovery(prefix_provider=lambda: ["192.168.1"], probe=probe, max_workers=1)

        result = discovery.scan("43871", configured_host="192.168.1.81")

        self.assertTrue(result["ok"])
        self.assertEqual(result["message"], "Found 1 Codex server(s).")
        self.assertEqual(result["devices"], [{"host": "192.168.1.81", "port": "43871", "label": "192.168.1.81:43871"}])
        self.assertEqual(calls.count("192.168.1.81"), 1)
        self.assertLess(calls.index("192.168.1.81"), calls.index("192.168.1.1"))

    def test_scan_reports_missing_lan_address(self) -> None:
        discovery = LanDiscovery(prefix_provider=lambda: [], probe=lambda _host, _port: None)

        result = discovery.scan("43871")

        self.assertEqual(
            result,
            {"ok": False, "message": "LAN IPv4 address not found on Steam Deck.", "devices": []},
        )

    def test_scan_reports_no_devices_on_port(self) -> None:
        discovery = LanDiscovery(prefix_provider=lambda: ["192.168.1"], probe=lambda _host, _port: None, max_workers=1)

        result = discovery.scan("43871")

        self.assertFalse(result["ok"])
        self.assertEqual(result["devices"], [])
        self.assertEqual(
            result["message"],
            "No Codex server on LAN port 43871. Start Codex App Server on the PC and allow it in firewall.",
        )


if __name__ == "__main__":
    unittest.main()
