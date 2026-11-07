"""Check public docs, SVG assets and general integration packaging offline."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ROOT / "README.md",
    ROOT / "README_RU.md",
    ROOT / "README_DE.md",
    ROOT / "README_ES.md",
    ROOT / "README_FR.md",
    ROOT / "README_ZH_CN.md",
    ROOT / "docs/ru/README.md",
    ROOT / "docs/ru/INSTALLATION.md",
    ROOT / "docs/ru/COMPATIBILITY.md",
    ROOT / "docs/ru/MIGRATION.md",
    ROOT / "docs/research/README.md",
    ROOT / "docs/research/HCI_CAPTURE_ANALYSIS.md",
    ROOT / "docs/LANGUAGE_POLICY.md",
    ROOT / "ROADMAP.md",
    ROOT / "docs/README.md",
    ROOT / "docs/STATUS.md",
    ROOT / "docs/INSTALLATION.md",
    ROOT / "docs/MIGRATION.md",
    ROOT / "docs/COMPATIBILITY.md",
    ROOT / "docs/MULTI_MODEL_ARCHITECTURE.md",
]


def test_general_domain_and_exactly_one_hacs_component():
    folder = ROOT / "custom_components"
    dirs = [x for x in folder.iterdir() if x.is_dir()]
    assert [x.name for x in dirs] == ["so_diffuser_ble"]
    manifest = json.loads((dirs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == dirs[0].name
    assert manifest["version"] == "1.0.0"
    assert len(manifest.get("bluetooth", [])) == 10
    assert all(x.get("local_name") and not any(
        wildcard in x["local_name"] for wildcard in ("*", "?")
    ) for x in manifest["bluetooth"])


def test_public_document_links_resolve():
    bad = []
    for file in PAGES:
        content = file.read_text(encoding="utf-8")
        for url in re.findall(r"!?(?:\[[^\]]*\])\(([^)]+)\)", content):
            link = url.split("#", 1)[0].strip().split(" ", 1)[0]
            if not link or link.startswith(("https://", "http://", "mailto:")):
                continue
            path = (file.parent / unquote(link)).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
                bad.append((file.relative_to(ROOT).as_posix(), link))
    assert not bad, f"Broken public docs links: {bad}"


def test_images_are_valid_editable_svg_not_external_tracking():
    for asset in ("hero.svg", "connection-flow.svg", "model-family.svg", "migration.svg", "control-preview.svg", "brand-icon.svg", "brand-logo.svg"):
        path = ROOT / "docs/assets" / asset
        raw = path.read_text(encoding="utf-8")
        root = ET.fromstring(raw)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib.get("viewBox")
        assert "<script" not in raw.lower()
        assert "http://" not in raw.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "https://" not in raw


def test_migration_documents_credential_retention():
    document = (ROOT / "docs/MIGRATION.md").read_text()
    assert "so_diffuser_ble" in document
    assert "so_s5" in document
    assert "so_s5_ble_tokens.json" in document
    assert "Backups" in document
    assert "core.config_entries" in document

def test_public_readmes_match_centered_github_reference_header():
    """Keep the six public README languages aligned with the centered header."""
    featured = (
        ("README.md", "English"),
        ("README_RU.md", "Русский"),
        ("README_DE.md", "Deutsch"),
        ("README_FR.md", "Français"),
        ("README_ES.md", "Español"),
        ("README_ZH_CN.md", "中文"),
    )
    all_readmes = tuple(path.name for path in ROOT.glob("README*.md"))
    assert set(all_readmes) == {
        "README.md", "README_RU.md", "README_DE.md", "README_FR.md",
        "README_ES.md", "README_ZH_CN.md",
    }
    expected_nav = '<p align="center">' + ' &nbsp;·&nbsp; '.join(
        f'<a href="{filename}">{label}</a>' for filename, label in featured
    ) + '</p>'
    for filename in all_readmes:
        content = (ROOT / filename).read_text(encoding="utf-8")
        lines = content.splitlines()
        assert lines[0].startswith('<p align="center"><img src="docs/assets/hero.svg"'), filename
        assert lines[0].endswith('width="100%"></p>'), filename
        assert lines[2] == expected_nav, filename
        assert lines[4] == '<p align="center">', filename
        assert lines[5].strip().startswith('<a href="https://github.com/Joka-kun/'), filename
        assert lines[8] == '</p>', filename
        assert lines[10] == '# Xiaomi SO Diffuser BLE', filename
        assert (ROOT / 'docs/assets/hero.svg').is_file(), filename
        assert '<details>' not in content and '<summary>' not in content, filename
        assert '<script' not in content.lower(), filename
        assert '🇬🇧' not in lines[2] and '🌐' not in lines[2], filename


def test_public_readmes_link_to_existing_six_languages():
    names = ("README.md", "README_RU.md", "README_DE.md",
             "README_ES.md", "README_FR.md", "README_ZH_CN.md")
    for filename in names:
        content = (ROOT / filename).read_text(encoding="utf-8")
        assert "so_s5" not in content, filename
        assert "SO Diffuser BLE" in content, filename
        assert (ROOT / filename).is_file(), filename
        for target in names:
            assert f'href="{target}"' in content, (filename, target)
    for obsolete in ("README_IT.md", "README_JA.md", "README_PT_BR.md"):
        assert not (ROOT / obsolete).exists(), obsolete


def test_ci_workflows_never_push_as_a_bot():
    assert not (ROOT / ".github/workflows/first-public-release.yml").exists()
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        assert "github-actions[bot]" not in text, workflow
        assert "git push" not in text and "git commit" not in text, workflow
        assert "contents: write" not in text, workflow


def test_docs_have_consistent_language_boundaries():
    """English technical prose is English; historical and localized sources stay separate."""
    english_docs = [
        ROOT / "README.md",
        ROOT / "ROADMAP.md",
        ROOT / "CHANGELOG.md",
        ROOT / "SECURITY.md",
        ROOT / "docs/README.md",
        ROOT / "docs/LANGUAGE_POLICY.md",
        ROOT / "docs/INSTALLATION.md",
        ROOT / "docs/COMPATIBILITY.md",
        ROOT / "docs/PROTOCOL.md",
        ROOT / "docs/MIGRATION.md",
        ROOT / "docs/CREDENTIALS.md",
        ROOT / "docs/MULTI_MODEL_ARCHITECTURE.md",
        ROOT / "docs/SPRAY_MODES_AND_COMPATIBILITY.md",
        ROOT / "docs/STATUS.md",
        ROOT / "docs/TESTING.md",
        ROOT / "docs/PUBLISHING.md",
        ROOT / "docs/research/README.md",
        ROOT / "docs/research/HCI_CAPTURE_ANALYSIS.md",
    ]
    for file in english_docs:
        content = file.read_text(encoding="utf-8")
        # Native-spelling language names within the language selector are intentional.
        content = re.sub(r'(?m)^<p align="center"><a href="README.md">English</a>.*?</p>\n', "", content)
        assert not re.search(r"[\u0400-\u04FF]", content), file.relative_to(ROOT)

    for filename in ("README_RU.md", "README_DE.md", "README_ES.md",
                     "README_FR.md", "README_ZH_CN.md"):
        content = (ROOT / filename).read_text(encoding="utf-8")
        content = re.sub(r'(?m)^<p align="center"><a href="README.md">English</a>.*?</p>\n', "", content)
        for stale_caption in (
            "[Installation](", "[Compatibility](", "[Research](",
            "[Status](", "[Roadmap](", "[Documentation index](",
        ):
            assert stale_caption not in content, (filename, stale_caption)

    russian_readme = (ROOT / "README_RU.md").read_text(encoding="utf-8")
    for target in ("docs/ru/INSTALLATION.md", "docs/ru/COMPATIBILITY.md",
                   "docs/ru/MIGRATION.md"):
        assert f"({target})" in russian_readme

    assert "272 AES-CCM tags" in (
        ROOT / "docs/research/HCI_CAPTURE_ANALYSIS.md"
    ).read_text(encoding="utf-8")
    assert "Дата обновления:" in (
        ROOT / "docs/ru/research/HCI_CAPTURE_ANALYSIS.md"
    ).read_text(encoding="utf-8")

def test_published_brand_assets_are_correct_dimensions():
    from PIL import Image

    brand = ROOT / "custom_components/so_diffuser_ble/brand"
    for filename, size in (
        ("icon.png", (256, 256)),
        ("icon@2x.png", (512, 512)),
        ("logo.png", (720, 240)),
        ("logo@2x.png", (960, 320)),
    ):
        with Image.open(brand / filename) as image:
            assert image.format == "PNG"
            assert image.size == size
            assert image.mode == "RGBA"


def test_first_public_release_metadata_is_consistent():
    manifest = json.loads(
        (ROOT / "custom_components/so_diffuser_ble/manifest.json").read_text()
    )
    assert manifest["version"] == "1.0.0"
    assert "first public GitHub Release" in (
        ROOT / "docs/RELEASE_NOTES.md"
    ).read_text(encoding="utf-8")
    assert (ROOT / "docs/BRANDING.md").is_file()
