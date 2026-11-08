import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "diagnostics"))

import unittest

from gatt_probe import bluez_options


class BluezOptionsTest(unittest.TestCase):
    def test_explicit_adapter_is_forwarded_to_bleak(self):
        self.assertEqual(bluez_options("hci0"), {"bluez": {"adapter": "hci0"}})

    def test_none_keeps_bleak_default(self):
        self.assertEqual(bluez_options(None), {})


if __name__ == "__main__":
    unittest.main()
