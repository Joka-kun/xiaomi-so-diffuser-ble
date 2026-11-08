"""Ensure credential migration cannot leak tokens or overwrite other S5s."""
from __future__ import annotations

import os
from pathlib import Path
import stat
import tempfile
import unittest

from custom_components.so_diffuser_ble.credentials import TokenFileError
from custom_components.so_diffuser_ble.token_store import (
    PRIVATE_FILENAME,
    has_device_token,
    load_device_token,
    save_device_token,
)

ADDRESS1 = "AA:BB:CC:DD:EE:01"
ADDRESS2 = "AA:BB:CC:DD:EE:02"
TOKEN1 = bytes.fromhex("0102030405060708090a0b0c")
TOKEN2 = bytes.fromhex("aabbccddeeff001122334455")


class TokenStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.file = self.base / ".storage" / PRIVATE_FILENAME

    def test_multiple_devices_private_mode_and_restart(self):
        save_device_token(self.base, ADDRESS1, TOKEN1)
        save_device_token(self.base, ADDRESS2, TOKEN2)
        self.assertEqual(load_device_token(self.base, ADDRESS1), TOKEN1)
        self.assertEqual(load_device_token(self.base, ADDRESS2), TOKEN2)
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode), 0o600)
        self.assertTrue(has_device_token(self.base, ADDRESS1))
        self.assertNotIn("oauth", self.file.read_text().lower())

    def test_existing_legacy_token_stays_untouched(self):
        legacy = self.base / "so_s5_token"
        legacy.write_text(TOKEN1.hex())
        legacy.chmod(0o600)
        self.assertEqual(load_device_token(self.base, ADDRESS1), TOKEN1)
        save_device_token(self.base, ADDRESS1, TOKEN2)
        self.assertEqual(load_device_token(self.base, ADDRESS1), TOKEN2)
        self.assertEqual(legacy.read_text(), TOKEN1.hex())
        self.assertEqual(load_device_token(self.base, ADDRESS2), TOKEN1)

    def test_missing_token_still_fails_closed(self):
        with self.assertRaises(TokenFileError):
            load_device_token(self.base, ADDRESS1)

    def test_wrong_length_cannot_be_saved(self):
        with self.assertRaises(ValueError):
            save_device_token(self.base, ADDRESS1, bytes(16))
        self.assertFalse(self.file.exists())

    def test_existing_store_with_insecure_permissions_is_rejected(self):
        save_device_token(self.base, ADDRESS1, TOKEN1)
        self.file.chmod(0o644)
        with self.assertRaises(TokenFileError):
            load_device_token(self.base, ADDRESS1)
        with self.assertRaises(TokenFileError):
            save_device_token(self.base, ADDRESS2, TOKEN2)

    @unittest.skipUnless(hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"), "POSIX FIFO required")
    def test_fifo_store_does_not_block_token_reads_or_writes(self):
        # O_RDONLY without O_NONBLOCK blocks indefinitely waiting for a writer.
        self.file.parent.mkdir()
        os.mkfifo(self.file, 0o600)
        with self.assertRaises(TokenFileError) as read:
            load_device_token(self.base, ADDRESS1)
        self.assertEqual(read.exception.reason, "type")
        with self.assertRaises(TokenFileError) as write:
            save_device_token(self.base, ADDRESS1, TOKEN1)
        self.assertEqual(write.exception.reason, "type")
        self.assertTrue(self.file.is_fifo())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW required")
    def test_symlinked_store_is_rejected(self):
        target = self.base / "outside.json"
        target.write_text('{"version":1,"devices":{}}')
        self.file.parent.mkdir()
        self.file.symlink_to(target)
        with self.assertRaises(OSError):
            load_device_token(self.base, ADDRESS1)
        self.assertFalse(self.file.is_file() and not self.file.is_symlink())


if __name__ == "__main__":
    unittest.main()
