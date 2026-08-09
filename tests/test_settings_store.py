import json
import tempfile
import unittest
from pathlib import Path

from codex_remote.domain.defaults import DEFAULT_SETTINGS
from codex_remote.domain.models import normalize_settings
from codex_remote.infrastructure.settings_store import SettingsStore


class SettingsStoreTest(unittest.TestCase):
    def test_normalize_settings_coerces_values_and_keeps_defaults(self) -> None:
        settings = normalize_settings({"host": " 192.168.1.81 ", "port": 43871, "token": " abc ", "autoRefresh": 0})

        self.assertEqual(
            settings,
            {
                "host": "192.168.1.81",
                "port": "43871",
                "token": "abc",
                "autoRefresh": False,
            },
        )

    def test_read_missing_file_returns_default_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SettingsStore(Path(tmp) / "settings.json")

            settings = store.read()
            settings["host"] = "changed"

            self.assertEqual(store.read(), DEFAULT_SETTINGS)

    def test_write_creates_parent_and_persists_normalized_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "settings.json"
            store = SettingsStore(path)

            written = store.write({"host": " pc.local ", "port": 43871, "token": " tok "})

            self.assertEqual(written["host"], "pc.local")
            self.assertEqual(written["port"], "43871")
            self.assertEqual(written["token"], "tok")
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), written)

    def test_read_invalid_json_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{broken", encoding="utf-8")

            self.assertEqual(SettingsStore(path).read(), DEFAULT_SETTINGS)


if __name__ == "__main__":
    unittest.main()
