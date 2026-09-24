from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_static_site_files_exist():
    for name in ["index.html", "styles.css", "app.js"]:
        assert (ROOT / "site" / name).is_file()


def test_site_has_analysis_button_and_theme_control():
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert 'id="analyseButton"' in html
    assert "Analyse reporting" in html
    assert 'id="themeToggle"' in html
    assert "Content-Security-Policy" in html


def test_site_javascript_avoids_common_injection_primitives():
    js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
    assert "eval(" not in js
    assert ".innerHTML" not in js
    assert "document.write" not in js


def test_site_has_all_42_checklist_keys():
    js = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
    marker = "const checklistItems = ["
    assert marker in js
    checklist_region = js.split(marker, 1)[1].split("];", 1)[0]
    assert checklist_region.count("key:") == 42
