import unittest

from codex_remote.infrastructure.diagnostics import ConnectivityDiagnostics


class ConnectivityDiagnosticsTest(unittest.TestCase):
    def test_reports_ready_lan_endpoint_without_proxy(self) -> None:
        diagnostics = ConnectivityDiagnostics(
            proxy_probe=lambda host, port: True,
            vpn_probe=lambda: False,
        )

        result = diagnostics.run({
            "host": "192.168.1.10",
            "port": "43871",
            "token": "token",
            "proxyEnabled": False,
        })

        self.assertTrue(result["ok"])
        self.assertEqual([check["status"] for check in result["checks"]], ["ok", "ok", "skipped", "skipped"])

    def test_reports_proxy_failure_when_proxy_mode_is_enabled(self) -> None:
        diagnostics = ConnectivityDiagnostics(
            proxy_probe=lambda host, port: False,
            vpn_probe=lambda: True,
        )

        result = diagnostics.run({
            "serverUrl": "wss://relay.example/ws",
            "token": "token",
            "proxyEnabled": True,
            "proxyHost": "127.0.0.1",
            "proxyPort": "12334",
        })

        self.assertFalse(result["ok"])
        self.assertEqual(result["checks"][2]["status"], "failed")
        self.assertEqual(result["checks"][3]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
