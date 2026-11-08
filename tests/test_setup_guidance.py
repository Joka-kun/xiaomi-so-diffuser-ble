"""Protect concise HA onboarding copy and the S5 light-effect UX."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "so_diffuser_ble"


def _translations(language):
    return json.loads((INTEGRATION / "translations" / f"{language}.json").read_text(encoding="utf-8"))


def test_cloud_selection_stays_short_and_no_longer_claims_s5_is_the_only_verified_one():
    ru = _translations("ru")["config"]["step"]["cloud_device"]["description"]
    en = _translations("en")["config"]["step"]["cloud_device"]["description"]
    assert "Только S5 проверен" not in ru
    assert "Only S5 has field-confirmed" not in en
    assert len(ru) < 260 and len(en) < 230
    assert "Mi Home" in ru and "Mi Home" in en
    assert "Bluetooth" in ru and "Bluetooth" in en


def test_oauth_redirect_help_is_part_of_the_actual_flow():
    for language in ("ru", "en"):
        flow = _translations(language)["config"]["progress"]["oauth"]
        assert "{link_left}" in flow and "{link_right}" in flow
        assert "{default_host}" in flow
        assert "{example_host}" in flow
        assert "Enter" in flow
        # URLs come from description placeholders (Hassfest disallows raw URLs).
        assert "http://" not in flow and "https://" not in flow
    source = (INTEGRATION / "config_flow.py").read_text(encoding="utf-8")
    assert '"default_host": OAUTH_REDIRECT_BASE' in source
    assert '"example_host": "http://192.168.1.50:8123"' in source


def test_ble_connection_and_auth_errors_are_distinct_and_actionable():
    for language in ("ru", "en"):
        error = _translations(language)["config"]["error"]
        assert "ble_connection_failed" in error
        assert "ble_auth_failed" in error
        assert "Mi Home" in error["ble_connection_failed"]
        assert "Bluetooth" in error["ble_connection_failed"]
        assert error["ble_connection_failed"] != error["ble_auth_failed"]


def test_light_declares_home_assistant_effect_feature():
    source = (INTEGRATION / "light.py").read_text(encoding="utf-8")
    assert "LightEntityFeature.EFFECT" in source
    assert "LIGHT_GRADIENT_ON" in source
    assert "ColorMode.ONOFF" in source
    assert 'EFFECT_GRADIENT = "Автоматический градиент"' in source


def test_work_mode_retains_entity_unique_key_and_raw_command_mapping():
    source = (INTEGRATION / "switch.py").read_text(encoding="utf-8")
    assert 'coordinator, "power", "Вкл/Выкл"' in source
    assert "async_set_power(True)" in source
    assert "async_set_power(False)" in source
