import unittest

from codex_remote.domain.models import endpoint_configured, proxy_config, readyz_url


class ConnectionSettingsTest(unittest.TestCase):
    def test_endpoint_configured_accepts_server_url_without_lan_host(self) -> None:
        settings = {"serverUrl": "wss://relay.example/codex", "host": "", "port": "43871"}

        self.assertTrue(endpoint_configured(settings))

    def test_readyz_url_derives_https_probe_from_wss_server_url(self) -> None:
        settings = {"serverUrl": "wss://relay.example/codex/ws?device=deck", "host": "", "port": "43871"}

        self.assertEqual(readyz_url(settings), "https://relay.example/readyz")

    def test_proxy_config_returns_none_when_disabled(self) -> None:
        self.assertIsNone(proxy_config({"proxyEnabled": False}))

    def test_proxy_config_returns_normalized_http_connect_proxy(self) -> None:
        settings = {"proxyEnabled": True, "proxyHost": " 127.0.0.1 ", "proxyPort": " 12334 "}

        self.assertEqual(proxy_config(settings), {"host": "127.0.0.1", "port": "12334"})


if __name__ == "__main__":
    unittest.main()
