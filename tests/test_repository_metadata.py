import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "so_diffuser_ble"


def _keys(value):
    if isinstance(value, dict):
        return {key: _keys(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_keys(child) for child in value]
    return type(value).__name__


class RepositoryMetadataTests(unittest.TestCase):
    def test_manifest_has_standalone_hacs_fields_and_links(self):
        manifest = json.loads((INTEGRATION / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], "so_diffuser_ble")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertGreaterEqual(tuple(map(int, manifest["version"].split("."))), (0, 3, 1))
        for key in ("documentation", "issue_tracker", "codeowners", "name"):
            self.assertIn(key, manifest)
        self.assertEqual(manifest["documentation"], "https://github.com/Joka-kun/xiaomi-so-diffuser-ble")
        self.assertEqual(manifest["issue_tracker"], "https://github.com/Joka-kun/xiaomi-so-diffuser-ble/issues")
        self.assertEqual(manifest["codeowners"], ["@Joka-kun"])

    def test_hacs_manifest_renders_readme(self):
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(hacs["name"], "Xiaomi SO Diffuser BLE")
        self.assertTrue(hacs["render_readme"])

    def test_custom_integration_ships_finished_translations_not_strings_json(self):
        en = json.loads((INTEGRATION / "translations" / "en.json").read_text())
        ru = json.loads((INTEGRATION / "translations" / "ru.json").read_text())
        self.assertEqual(_keys(en), _keys(ru))
        self.assertFalse((INTEGRATION / "strings.json").exists())

    def test_brand_icon_is_a_256_square_png(self):
        icon = (INTEGRATION / "brand" / "icon.png").read_bytes()
        self.assertEqual(icon[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(int.from_bytes(icon[16:20], "big"), 256)
        self.assertEqual(int.from_bytes(icon[20:24], "big"), 256)

    def test_repository_contains_exactly_one_custom_integration(self):
        integrations = [path for path in (ROOT / "custom_components").iterdir() if path.is_dir()]
        self.assertEqual([path.name for path in integrations], ["so_diffuser_ble"])


if __name__ == "__main__":
    unittest.main()
