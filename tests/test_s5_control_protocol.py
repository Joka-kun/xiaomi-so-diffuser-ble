import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.so_diffuser_ble.credentials import TokenFileError, load_token_file
from custom_components.so_diffuser_ble.config import validate_ble_address
from custom_components.so_diffuser_ble.protocol import (
    decode_token_hex,
    encode_fixed_property_set,
    encode_power_set,
    encrypt_tx_parcel,
    light_brightness_to_ha,
    light_is_gradient,
    light_is_on,
    light_value_from_ha_brightness,
    light_value_off,
    light_value_restore,
    parse_set_property_response,
)


class S5ControlProtocolTests(unittest.TestCase):
    def test_token_file_is_exact_24_digit_hex(self):
        self.assertEqual(decode_token_hex("000102030405060708090a0b"), bytes(range(12)))
        for invalid in ("000102030405060708090a0b\n", "000102030405060708090a0", "000102030405060708090a0bxx"):
            with self.subTest(invalid_length=len(invalid)), self.assertRaises(ValueError):
                decode_token_hex(invalid)

    def test_power_set_encoding_uses_bundle_schema_candidate_uint8(self):
        self.assertEqual(encode_power_set(43, True), bytes.fromhex("0c202b00000102ec03011001"))
        self.assertEqual(encode_power_set(43, False), bytes.fromhex("0c202b00000102ec03011000"))
        with self.assertRaises(ValueError):
            encode_power_set(65536, True)
        with self.assertRaises(TypeError):
            encode_power_set(43, 1)

    def test_fixed_ui_property_encodings_are_exact_and_allowlisted(self):
        vectors = {
            "fragrance_out_time": (9, "0c202b000001030300011009"),
            "idle_time": (3, "0c202b000001030400011003"),
            "light": (238, "0c202b0000010308000110ee"),
            "color": (0x123456, "0f202b000001030900045056341200"),
        }
        for name, (value, expected_hex) in vectors.items():
            with self.subTest(property=name):
                self.assertEqual(encode_fixed_property_set(43, name, value), bytes.fromhex(expected_hex))

    def test_fixed_ui_property_encoding_rejects_unknown_and_out_of_range_values(self):
        for name, value in (
            ("arbitrary", 1),
            ("idle_time", 1),
            ("idle_time", 2),
            ("auto_power_time", 2054),
            ("repeat", 255),
            ("light", 101),
            ("light", 229),
            ("color", 0x1000000),
        ):
            with self.subTest(property=name, value=value), self.assertRaises(ValueError):
                encode_fixed_property_set(43, name, value)

    def test_light_encoder_accepts_values_emitted_by_bundle_switches(self):
        for value in (0, 80, 110, 128, 208, 228, 238):
            with self.subTest(value=value):
                packet = encode_fixed_property_set(43, "light", value)
                self.assertEqual(packet[-1], value)


    def test_light_brightness_round_trip_uses_vendor_1_to_100_scale(self):
        self.assertEqual(light_value_from_ha_brightness(1), 129)
        self.assertEqual(light_value_from_ha_brightness(255), 228)
        self.assertEqual(light_brightness_to_ha(129), 3)
        self.assertEqual(light_brightness_to_ha(228), 255)
        for value in (None, 0, 100, 110, 238):
            with self.subTest(value=value):
                self.assertIsNone(light_brightness_to_ha(value))
        with self.assertRaises(ValueError):
            light_value_from_ha_brightness(0)

    def test_light_off_clears_enable_bit_and_restore_keeps_selected_mode(self):
        self.assertTrue(light_is_on(228))
        self.assertTrue(light_is_gradient(238))
        self.assertFalse(light_is_on(110))
        self.assertEqual(light_value_off(228), 100)
        self.assertEqual(light_value_off(238), 110)
        self.assertEqual(light_value_off(None), 0)
        self.assertEqual(light_value_restore(50), 178)
        self.assertEqual(light_value_restore(110), 238)
        self.assertEqual(light_value_restore(None), 228)

    def test_set_response_matches_s5_capture_layout(self):
        transaction_id, results = parse_set_property_response(bytes.fromhex("0b202b0001010305000000"))
        self.assertEqual(transaction_id, 43)
        self.assertEqual(results, ((3, 5, 0),))

    def test_token_file_loads_private_exact_hex_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("000102030405060708090a0b", encoding="ascii")
            path.chmod(0o600)
            self.assertEqual(load_token_file(path), bytes(range(12)))

    def test_token_file_rejects_group_or_world_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("000102030405060708090a0b", encoding="ascii")
            for mode in (0o644, 0o700, 0o000):
                with self.subTest(mode=oct(mode)):
                    path.chmod(mode)
                    with self.assertRaises(TokenFileError) as caught:
                        load_token_file(path)
                    self.assertEqual(caught.exception.reason, "permissions")
                    self.assertNotIn("000102030405060708090a0b", str(caught.exception))

    def test_token_file_rejects_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "token"
            os.mkfifo(fifo, 0o600)
            project = str(Path(__file__).resolve().parents[1])
            code = (
                "import sys; sys.path.insert(0, sys.argv[1]); "
                "from custom_components.so_diffuser_ble.credentials import TokenFileError, load_token_file; "
                "\ntry: load_token_file(sys.argv[2])\n"
                "except TokenFileError as error: print(error.reason)"
            )
            result = subprocess.run(
                [sys.executable, "-c", code, project, str(fifo)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "type")

    def test_token_file_rejects_newline_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("000102030405060708090a0b\n", encoding="ascii")
            path.chmod(0o600)
            with self.assertRaises(TokenFileError) as caught:
                load_token_file(path)
            self.assertEqual(caught.exception.reason, "format")
            path.unlink()
            with self.assertRaises(TokenFileError) as caught:
                load_token_file(path)
            self.assertEqual(caught.exception.reason, "missing")

    def test_ble_address_validation_is_strict_and_preserves_case(self):
        address = "aA:bB:cC:dD:eE:fF"
        self.assertEqual(validate_ble_address(address), address)
        for invalid in ("aa:bb:cc:dd:ee", "aa-bb-cc-dd-ee-ff", "not-an-address", address + "\n"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_ble_address(invalid)

    @unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography required")
    def test_tx_parcel_matches_aes_ccm_fixed_vector(self):
        parcel = encrypt_tx_parcel(
            bytes(range(16)),
            bytes.fromhex("a0a1a2a3"),
            1,
            bytes.fromhex("0c20340000010307000110ff"),
        )
        self.assertEqual(parcel.hex(), "0100010001dc4a31be547aa85331b14842ccad73")


if __name__ == "__main__":
    unittest.main()
