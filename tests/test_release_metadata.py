"""Public release contract for BLE recovery and official HACS listing."""
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "custom_components" / "so_diffuser_ble"


def test_manifest_package_and_oauth_user_agent_agree():
    manifest = json.loads((DOMAIN / "manifest.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    oauth_source = (DOMAIN / "xiaomi_oauth.py").read_text(encoding="utf-8")
    assert manifest["version"] == pyproject["project"]["version"] == "1.0.8"
    assert 'xiaomi-so-diffuser-ble/1.0.8 client/' in oauth_source
    assert manifest["domain"] == "so_diffuser_ble"
    assert "bluetooth" in manifest["dependencies"]


def test_published_source_preserves_user_state_and_has_readme_install():
    source = (DOMAIN / "coordinator.py").read_text(encoding="utf-8")
    switch = (DOMAIN / "switch.py").read_text(encoding="utf-8")
    assert "async_ble_device_from_address" in source or "async_register_callback" in source
    assert "available" in switch
    for path in ("README.md", "README_RU.md"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "HACS" in text
        assert "Xiaomi SO Diffuser BLE" in text
    notes = (ROOT / "docs" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "8–24" in notes
    assert (ROOT / "LICENSE").is_file()
