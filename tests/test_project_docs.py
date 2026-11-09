"""Check public docs, SVG assets and general integration packaging offline."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted({
    ROOT / "CHANGELOG.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "ROADMAP.md",
    ROOT / "SECURITY.md",
    *ROOT.glob("README*.md"),
    *(ROOT / "docs").glob("*.md"),
    *(ROOT / "docs" / "ru").glob("*.md"),
    *(ROOT / "docs" / "research").glob("*.md"),
    *(ROOT / "docs" / "ru" / "research").glob("*.md"),
})


def test_general_domain_and_exactly_one_hacs_component():
    folder = ROOT / "custom_components"
    dirs = [x for x in folder.iterdir() if x.is_dir()]
    assert [x.name for x in dirs] == ["so_diffuser_ble"]
    manifest = json.loads((dirs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == dirs[0].name
    assert manifest["version"] == "1.0.5"
    assert len(manifest.get("bluetooth", [])) == 10
    assert all(x.get("local_name") and not any(
        wildcard in x["local_name"] for wildcard in ("*", "?")
    ) for x in manifest["bluetooth"])


def test_public_document_links_resolve():
    bad = []
    for file in PAGES:
        content = file.read_text(encoding="utf-8")
        links = re.findall(r"!?(?:\[[^\]]*\])\(([^)]+)\)", content)
        links += re.findall(r'<img\s+[^>]*src="([^"]+)"', content)
        for url in links:
            link = url.split("#", 1)[0].strip().split(" ", 1)[0]
            if not link or link.startswith(("https://", "http://", "mailto:")):
                continue
            path = (file.parent / unquote(link)).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
                bad.append((file.relative_to(ROOT).as_posix(), link))
    assert not bad, f"Broken public docs links: {bad}"


def test_images_are_valid_editable_svg_not_external_tracking():
    for asset in ("hero.svg", "connection-flow.svg", "model-family.svg", "migration.svg", "control-preview.svg", "brand-icon.svg"):
        path = ROOT / "docs/assets" / asset
        raw = path.read_text(encoding="utf-8")
        root = ET.fromstring(raw)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib.get("viewBox")
        assert "<script" not in raw.lower()
        assert "http://" not in raw.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "https://" not in raw


def test_premium_artwork_is_consistent_and_honest():
    graphics = {
        "hero.svg": ("SO DIFFUSER", "BLE"),
        "connection-flow.svg": ("DISCOVER", "AUTHORIZE", "VERIFY", "CONTROL"),
        "control-preview.svg": ("POWER", "BACKLIGHT", "NOT A SCREENSHOT"),
        "migration.svg": ("BACK UP", "REMOVE OLD", "INSTALL NEW", "VERIFY"),
        "model-family.svg": ("FIELD-REPORTED", "OTHER MODEL PROFILES"),
    }
    for name, words in graphics.items():
        content = (ROOT / "docs/assets" / name).read_text(encoding="utf-8")
        assert 'role="img"' in content and 'aria-label="' in content, name
        assert "<title>" in content, name
        assert all(word in content for word in words), (name, words)
    icons = (ROOT / "docs/assets/brand-icon.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 512 512"' in icons
    assert "http://" not in icons.replace('xmlns="http://www.w3.org/2000/svg"', "")


def test_s5_reference_geometry_only_appears_on_hero():
    hero = (ROOT / "docs/assets/hero.svg").read_text(encoding="utf-8")
    for feature in ('id="s5-body"', 'id="s5-hero-display"', 'id="s5-hero-button"'):
        assert feature in hero
    family = (ROOT / "docs/assets/model-family.svg").read_text(encoding="utf-8")
    assert "SO S5" in family and "FIELD-REPORTED" in family
    assert "OTHER MODEL PROFILES" in family
    assert 'id="s5-display"' not in family
    assert 'id="s5-button"' not in family
    assert "url(#mist)" not in hero and "url(#mist)" not in family


def test_noir_artwork_has_motion_and_no_status_or_russian_in_images():
    visuals = (
        "hero.svg", "control-preview.svg", "model-family.svg",
        "overview.svg", "connection-flow.svg", "migration.svg",
        "brand-icon.svg",
    )
    import xml.etree.ElementTree as ET
    for name in visuals:
        svg = (ROOT / "docs/assets" / name).read_text(encoding="utf-8")
        ET.fromstring(svg)
        if name.startswith("brand-"):
            assert all(color in svg for color in ("#778289", "#B68E69", "#FFFFFF")), name
            assert all(feature in svg for feature in ('id="s5-body"', 'id="s5-display"', 'id="s5-button"')), name
            assert "<text " not in svg and '<rect width="512"' not in svg, name
        else:
            assert "#06090C" in svg and "#FFE2A6" in svg, name
        assert not re.search(r"experimental", svg, flags=re.I), name
        assert not re.search(r"[\u0400-\u04FF]", svg), name
        assert "http://" not in svg.replace('xmlns="http://www.w3.org/2000/svg"', ""), name
    hero = (ROOT / "docs/assets/hero.svg").read_text(encoding="utf-8")
    assert "rotate(-10" in hero and 'id="s5-hero-button"' in hero
    control = (ROOT / "docs/assets/control-preview.svg").read_text(encoding="utf-8")
    assert "BACKLIGHT" in control and "POWER" in control
    assert "LIGHT IN MOTION" in control and "s5-hero-button" not in control
    family = (ROOT / "docs/assets/model-family.svg").read_text(encoding="utf-8")
    assert family.count("model listing") == 8
    assert "S1 Pro" in family and "S19" in family
    assert 'id="s5-body"' not in family


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
    assert not (ROOT / ".github/workflows/publish-v1.0.1.yml").exists()
    assert not (ROOT / ".github/workflows/generate-brand-pngs.yml").exists()
    assert not (ROOT / ".github/workflows/publish-v1.0.2.yml").exists()
    assert not (ROOT / ".github/workflows/generate-ha-brand-pngs.yml").exists()
    assert not (ROOT / ".github/workflows/publish-v1.0.3.yml").exists()
    assert not (ROOT / ".github/workflows/generate-s5-icon-pngs.yml").exists()
    assert not (ROOT / ".github/workflows/publish-v1.0.4.yml").exists()
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        assert "github-actions[bot]" not in text, workflow
        assert "git push" not in text and "git commit" not in text, workflow
        assert "contents: write" not in text, workflow
        assert "  contents: read" in text, workflow
        assert "    branches: [main]" in text, workflow
        assert "  pull_request:" in text, workflow
        assert "  timeout-minutes: 20" in text, workflow
        assert "concurrency:" in text and "cancel-in-progress: true" in text, workflow
    weekly = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    assert '    - cron: "17 4 * * 1"' in weekly



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
    ):
        with Image.open(brand / filename) as image:
            assert image.format == "PNG"
            assert image.size == size
            assert image.mode == "RGBA"
        assert (brand / filename).stat().st_size <= 2 * 1024 * 1024, (
            "Marketplace brands service rejects images larger than 2 MiB"
        )


def test_s5_brand_is_transparent_and_uses_logo_fallback():
    """The standalone S5 mark must be legible at the HA tile size."""
    from PIL import Image
    brand = ROOT / "custom_components/so_diffuser_ble/brand"
    for name in ("logo.png", "logo@2x.png", "dark_logo.png", "dark_logo@2x.png"):
        assert not (brand / name).exists(), name
    for name, size in (("icon.png", 256), ("icon@2x.png", 512)):
        with Image.open(brand / name) as im:
            assert im.mode == "RGBA" and im.size == (size, size), name
            assert im.getpixel((0, 0))[3] == 0, name
            assert im.getpixel((size // 2, size // 2))[3] > 245, name
            bounds = im.getchannel("A").getbbox()
            assert bounds is not None and bounds[2] - bounds[0] >= size * .76, name


def test_published_release_metadata_is_consistent():
    manifest = json.loads(
        (ROOT / "custom_components/so_diffuser_ble/manifest.json").read_text()
    )
    assert manifest["version"] == "1.0.5"
    notes = (ROOT / "docs/RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert notes.startswith("# Xiaomi SO Diffuser BLE — v1.0.5")
    assert "First public release" not in notes
    assert (ROOT / "docs/BRANDING.md").is_file()


def test_public_readmes_use_one_product_image_without_decorative_panels():
    readmes = (
        "README.md", "README_RU.md", "README_DE.md",
        "README_FR.md", "README_ES.md", "README_ZH_CN.md",
    )
    for filename in readmes:
        source = (ROOT / filename).read_text(encoding="utf-8")
        assert source.count('src="docs/assets/hero.svg"') == 1, filename
        assert "![" not in source, filename
        for removed in ("control-preview.svg", "model-family.svg", "overview.svg"):
            assert f"docs/assets/{removed}" not in source, filename
        assert "S5" in source, filename

    # Keep support status as text, never communicate it through speculative graphics.
    for filename in ("docs/COMPATIBILITY.md", "docs/ru/COMPATIBILITY.md"):
        source = (ROOT / filename).read_text(encoding="utf-8")
        assert "bwj.diffuser.s5" in source
        assert "model-family.svg" not in source
        assert "product.webp" not in source
    assert "assets/overview.svg" not in (
        ROOT / "docs/README.md"
    ).read_text(encoding="utf-8")

    # Source artwork can stay in Git for provenance, without being embedded in the README.
    for filename in ("hero.svg", "overview.svg", "control-preview.svg",
                     "model-family.svg", "connection-flow.svg", "brand-icon.svg",
                     "migration.svg"):
        source = (ROOT / "docs/assets" / filename).read_text(encoding="utf-8")
        assert not re.search(r"[\u0400-\u04FF]", source), filename


def test_photo_style_noir_sources_are_small_and_valid():
    from PIL import Image
    expected = {
        "hero.webp": (1440, 480),
        "overview.webp": (1280, 720),
        "setup.webp": (1280, 720),
        "controls.webp": (1280, 720),
        "product.webp": (1024, 1024),
    }
    for name, size in expected.items():
        file = ROOT / "docs/assets" / name
        assert file.stat().st_size < 180_000, name
        with Image.open(file) as image:
            assert image.format == "WEBP", name
            assert image.size == size, name
            image.verify()


def test_brand_pngs_match_rendered_noir_sources():
    from PIL import Image, ImageChops
    from tools.build_brand_assets import BRAND_IMAGES, render_svg
    brand = ROOT / "custom_components/so_diffuser_ble/brand"
    for png, source, size in BRAND_IMAGES:
        expected = render_svg(source, size)
        with Image.open(brand / png) as image:
            actual = image.convert("RGBA")
            assert image.mode == "RGBA" and image.size == size
            assert ImageChops.difference(actual, expected).getbbox() is None, png

    # Different square and wide compositions; same recognizable device.
    icon_svg = (ROOT / "docs/assets/brand-icon.svg").read_text()
    assert all(f in icon_svg for f in ("s5-body", "s5-display", "s5-button", "s5-rim"))
    assert "<text " not in icon_svg

def test_four_stage_artwork_is_additive():
    """Keep original brand cover and SVG guide when adding the author-provided image."""
    import hashlib
    from PIL import Image
    path = ROOT / "docs/assets/connection-four-steps.png"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "244c47e8571025a8661fac9cf0e238a001288b09c63db84a18ff2c9a97817e65"
    with Image.open(path) as artwork:
        assert artwork.format == "PNG"
        assert artwork.size == (2048, 682)
        artwork.verify()
    for filename in ("README.md", "README_RU.md", "README_DE.md", "README_ES.md", "README_FR.md", "README_ZH_CN.md"):
        content = (ROOT / filename).read_text(encoding="utf-8")
        assert content.count('docs/assets/hero.svg') == 1
        assert content.count('docs/assets/connection-four-steps.png') == 1
        assert "control-preview.svg" not in content
    for name, prefix in (("docs/INSTALLATION.md", "assets/"), ("docs/ru/INSTALLATION.md", "../assets/")):
        content = (ROOT / name).read_text(encoding="utf-8")
        assert prefix + "connection-flow.svg" in content
        assert prefix + "connection-four-steps.png" in content


def test_public_repository_hygiene_and_safe_contribution_path():
    """Keep contributor entry points and localized README presentation tidy."""
    readmes = (
        "README.md", "README_RU.md", "README_DE.md",
        "README_FR.md", "README_ES.md", "README_ZH_CN.md",
    )
    headings = ("Features", "Возможности", "Funktionen", "Fonctionnalités", "Funciones", "功能")
    for name, heading in zip(readmes, headings):
        source = (ROOT / name).read_text(encoding="utf-8")
        assert "\n\n\n" not in source, name
        assert "| <span>" not in source, name
        assert f"## {heading}" in source, name
        assert "https://github.com/Joka-kun/xiaomi-so-diffuser-ble" in source, name
        assert source.count('docs/assets/hero.svg') == 1, name
        assert source.count('docs/assets/connection-four-steps.png') == 1, name
    for relative in (
        "CONTRIBUTING.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ):
        assert (ROOT / relative).is_file(), relative
    guidelines = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "SECURITY.md" in guidelines and "docs/BRANDING.md" in guidelines
    branding = (ROOT / "docs/BRANDING.md").read_text(encoding="utf-8")
    assert "connection-four-steps.png" in branding
    assert "connection-flow.svg" in branding
    assert "WebP" in branding


def test_onboarding_illustration_precedes_matching_four_step_instructions():
    """README image should illustrate pairing, not redundantly depict HACS installation."""
    languages = {
        "README.md": ("### Connection in four steps", ("Discover", "Authorize", "Verify", "Control")),
        "README_RU.md": ("### Подключение в четыре этапа", ("Поиск", "Авторизация", "Проверка", "Управление")),
        "README_DE.md": ("### Verbindung in vier Schritten", ("Erkennen", "Autorisieren", "Verifizieren", "Steuern")),
        "README_FR.md": ("### Connexion en quatre étapes", ("Découvrir", "Autoriser", "Vérifier", "Contrôler")),
        "README_ES.md": ("### Conexión en cuatro pasos", ("Detectar", "Autorizar", "Verificar", "Controlar")),
        "README_ZH_CN.md": ("### 四步完成连接", ("发现设备", "授权登录", "验证连接", "本地控制")),
    }
    for name, (heading, actions) in languages.items():
        content = (ROOT / name).read_text(encoding="utf-8")
        image = '<p align="center"><img src="docs/assets/connection-four-steps.png"'
        assert content.count(image) == 1, name
        heading_index = content.index(heading)
        image_index = content.index(image)
        assert heading_index < image_index, name
        assert content.index("https://github.com/Joka-kun/xiaomi-so-diffuser-ble") < image_index, name
        steps = [content.index(f"{i}. **{action}**", image_index) for i, action in enumerate(actions, 1)]
        assert image_index < steps[0] < steps[1] < steps[2] < steps[3], name
        # Before the diagram, the instructions explain how to install HACS.
        assert "HACS" in content[content.index("## ", content.index("# Xiaomi SO Diffuser BLE") + 1):image_index], name
        # The top of each README and the existing SVG-based guide are unchanged.
        assert content.startswith('<p align="center"><img src="docs/assets/hero.svg"'), name
    for path in ("docs/INSTALLATION.md", "docs/ru/INSTALLATION.md"):
        content = (ROOT / path).read_text(encoding="utf-8")
        assert "connection-flow.svg" in content and "connection-four-steps.png" in content, path
