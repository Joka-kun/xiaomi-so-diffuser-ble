"""SO model capability registry: cloud visibility is not BLE compatibility."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from custom_components.so_diffuser_ble.models import (
    DEFAULT_MODEL, MODEL_PROFILES, advertised_model, assert_model_opt_in,
    get_profile,
)
from custom_components.so_diffuser_ble.xiaomi_oauth import extract_so_devices, extract_s5_devices


class SOModelRegistryTests(unittest.TestCase):
    def test_each_known_model_is_explicit_and_s5_remains_the_only_confirmed_one(self):
        self.assertEqual(len(MODEL_PROFILES), 9)
        self.assertEqual(
            {model for model, profile in MODEL_PROFILES.items() if profile.confirmed_gatt},
            {DEFAULT_MODEL},
        )
        self.assertFalse(get_profile().experimental)
        self.assertTrue(get_profile("bwj.diffuser.s6").experimental)
        with self.assertRaisesRegex(ValueError, "unknown_so_diffuser_model"):
            get_profile("xiaomi.diffuser.xw002")

    def test_experimental_models_require_explicit_true_even_when_in_config_entry(self):
        for model in MODEL_PROFILES:
            profile = get_profile(model)
            if profile.experimental:
                with self.subTest(model=model):
                    with self.assertRaisesRegex(ValueError, "explicit_opt_in"):
                        assert_model_opt_in(model, False)
                    self.assertIs(assert_model_opt_in(model, True), profile)
            else:
                self.assertIs(assert_model_opt_in(model, False), profile)

    def test_exact_discovery_names_never_accept_general_fe95_or_fake_prefixes(self):
        for model in MODEL_PROFILES:
            self.assertEqual(advertised_model(model.upper()), model)
        self.assertEqual(advertised_model("SO Smart Aroma Diffuser S5"), DEFAULT_MODEL)
        for bad in ("Mi Home", "bwj.diffuser.s6.extra", "bwj.diffuser", "xiaomi.diffuser.xw002", None):
            self.assertIsNone(advertised_model(bad))

    def test_profiles_split_light_no_light_temperature_and_unproven_longspray(self):
        self.assertFalse(get_profile("bwj.diffuser.s19").light)
        self.assertFalse(get_profile("bwj.diffuser.k09").light)
        self.assertTrue(get_profile("bwj.diffuser.s1pro").light)
        self.assertTrue(get_profile("bwj.diffuser.s1pro").temperature)
        self.assertTrue(get_profile(DEFAULT_MODEL).long_spray)
        self.assertTrue(all(p.long_spray for p in MODEL_PROFILES.values()))
        # The zero-pause register exists in all published schemas, but
        # physical LongSpray semantics remain unconfirmed on relatives.

    def test_cloud_parser_lists_only_known_models_without_claiming_auth_compatibility(self):
        token = "0102030405060708090a0b0c"
        page = {"list": [
            {"model": DEFAULT_MODEL, "did": "s5", "name": "S5", "token": token},
            {"model": "bwj.diffuser.s6", "did": "s6", "name": "S6", "token": token},
            {"model": "bwj.diffuser.s1pro", "did": "s1pro", "name": "S1Pro", "token": token},
            {"model": "bwj.diffuser.k09", "did": "s1", "name": "S1", "token": token},
            {"model": "xiaomi.diffuser.xw002", "did": "different-auth", "token": token},
            {"model": "bwj.diffuser.s9", "did": "malformed", "token": "wrong"},
        ]}
        result = extract_so_devices(page)
        self.assertEqual({x["did"] for x in result}, {"s5", "s6", "s1pro", "s1"})
        self.assertEqual(extract_s5_devices(page)[0]["did"], "s5")
        self.assertTrue(all(len(x["token"]) == 24 for x in result))


if __name__ == "__main__":
    unittest.main()
