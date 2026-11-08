import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "import_xiaomi_token.py"
spec = importlib.util.spec_from_file_location("import_xiaomi_token", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TOKEN = "00112233445566778899aabb"


class XiaomiTokenImportTests(unittest.TestCase):
    def test_selects_normalized_project_record(self):
        payload = [{"model": module.MODEL, "did": "device-001", "token": TOKEN, "ble_key": "f" * 32}]
        self.assertEqual(module.select_device(payload)["token"], TOKEN)

    def test_selects_nested_upstream_export_record(self):
        payload = [{"server": "cn", "homes": [{"devices": [
            {"model": "other.model", "did": "other", "token": TOKEN},
            {"model": module.MODEL, "did": "s5-001", "token": TOKEN, "BLE_DATA": {"beaconkey": "f" * 32}},
        ]}]}]
        self.assertEqual(module.select_device(payload)["did"], "s5-001")

    def test_requires_did_when_multiple_s5_devices_exist(self):
        payload = [
            {"model": module.MODEL, "did": "device-001", "token": TOKEN},
            {"model": module.MODEL, "did": "device-002", "token": TOKEN},
        ]
        with self.assertRaisesRegex(ValueError, "pass --did"):
            module.select_device(payload)
        self.assertEqual(module.select_device(payload, did="device-002")["did"], "device-002")

    def test_rejects_missing_or_wrong_length_token(self):
        for value in (None, "f" * 32, "z" * 24, "a" * 23):
            payload = [{"model": module.MODEL, "did": "s5", "token": value}]
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.select_device(payload)

    def test_writes_exact_token_without_newline_and_mode_0600(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "so_s5_token"
            module.write_token(path, TOKEN)
            self.assertEqual(path.read_text(encoding="ascii"), TOKEN)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_refuses_overwrite_without_explicit_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "so_s5_token"
            path.write_text(TOKEN, encoding="ascii")
            with self.assertRaises(FileExistsError):
                module.write_token(path, "ffeeddccbbaa998877665544")
            module.write_token(path, "ffeeddccbbaa998877665544", replace=True)
            self.assertEqual(path.read_text(encoding="ascii"), "ffeeddccbbaa998877665544")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_rejects_symlink_even_when_replace_is_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text(TOKEN, encoding="ascii")
            link = root / "token"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                module.write_token(link, "ffeeddccbbaa998877665544", replace=True)
            self.assertEqual(target.read_text(encoding="ascii"), TOKEN)


if __name__ == "__main__":
    unittest.main()
