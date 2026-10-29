"""Tests for the Plain-English IP Guide build and content.

Run with:  pytest
"""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SITE_DIR = ROOT / "site"
LICENSE_PATH = ROOT / "LICENSE"
README_PATH = ROOT / "README.md"

REQUIRED_SLUGS = [
    "01-copyright-the-moment-you-publish",
    "02-what-registration-buys",
    "03-fair-use-and-quote-myths",
    "04-public-domain-and-creative-commons",
    "05-licensing-music-and-fonts",
    "06-accidental-reuse",
    "07-trademark-basics-for-series-names",
    "checklist",
    "glossary",
]

EXACT_LICENSE_LINE = "Copyright (c) 2026 Asdale Dynamics, LLC"

# Text patterns that must never appear in committed files.
SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",              # AWS access key id
    r"ghp_[A-Za-z0-9]{20,}",          # GitHub personal access token
    r"sk-[A-Za-z0-9-]{20,}",          # OpenAI-style secret key
    r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9]{16,}",
    r"(?i)password\s*=\s*['\"][^'\"]{6,}",
]


def build() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "build.py"], cwd=ROOT, capture_output=True, text=True
    )


def check() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "build.py", "--check"], cwd=ROOT, capture_output=True, text=True
    )


# ---------------------------------------------------------------- build works


def test_check_mode_passes() -> None:
    result = check()
    assert result.returncode == 0, result.stderr or result.stdout


def test_build_succeeds_and_is_fresh() -> None:
    result = build()
    assert result.returncode == 0, result.stderr or result.stdout
    for slug in REQUIRED_SLUGS:
        page = SITE_DIR / f"{slug}.html"
        assert page.is_file(), f"missing built page {slug}"
    assert (SITE_DIR / "index.html").is_file()
    assert (SITE_DIR / "style.css").is_file()
    assert (SITE_DIR / "permission-log.csv").is_file()


def test_built_index_lists_all_guides() -> None:
    index = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    for slug in REQUIRED_SLUGS:
        assert f"{slug}.html" in index, f"index does not link to {slug}"


def test_built_pages_are_well_formed_html() -> None:
    for page in sorted(SITE_DIR.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        assert text.startswith("<!DOCTYPE html>"), page.name
        assert text.rstrip().endswith("</html>"), page.name
        # Balanced main structural tags.
        for tag in ("html", "head", "body", "main"):
            open_count = len(re.findall(rf"<{tag}[ >]", text))
            close_count = text.count(f"</{tag}>")
            assert open_count == close_count == 1, f"{page.name}: unbalanced <{tag}>"


def test_built_pages_links_resolve() -> None:
    for page in SITE_DIR.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"#:?]+)"', text):
            if href.startswith(("http", "mailto", "//")):
                continue
            target = page.parent / href
            assert target.exists(), f"{page.name}: broken link {href}"


def test_pristine_rebuild_works() -> None:
    """The build works even if site/ is deleted: regenerate from scratch."""
    result = check()
    assert result.returncode == 0, result.stderr or result.stdout
    shutil.rmtree(SITE_DIR)
    result = build()
    assert result.returncode == 0, result.stderr or result.stdout


def test_site_rebuilt_in_pristine_run_is_complete() -> None:
    # Depends on test_pristine_rebuild_works having re-created site/.
    for slug in REQUIRED_SLUGS:
        assert (SITE_DIR / f"{slug}.html").is_file(), f"missing rebuilt page {slug}"


# ------------------------------------------------------------- content checks


def test_license_has_exact_copyright_line() -> None:
    text = LICENSE_PATH.read_text(encoding="utf-8")
    assert EXACT_LICENSE_LINE in text
    assert text.startswith("MIT License")
    assert "Permission is hereby granted" in text


def test_readme_credits_llc_and_explains_how_to_run() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    assert "Asdale Dynamics, LLC" in text
    assert "python3 build.py" in text
    assert "pytest" in text
    assert "never legal advice" in text.lower()


def test_every_doc_carries_the_disclaimer() -> None:
    for doc in sorted(DOCS_DIR.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        assert "never legal advice" in text.lower(), f"{doc.name}: no disclaimer"


def test_topic_coverage_keywords_present() -> None:
    """Each required topic is genuinely covered in its guide."""
    keywords = {
        "01-copyright-the-moment-you-publish": ["fixed in a tangible form", "© notice"],
        "02-what-registration-buys": ["statutory damages", "copyright.gov"],
        "03-fair-use-and-quote-myths": ["four factors", "attribution", "30 words"],
        "04-public-domain-and-creative-commons": ["CC0", "CC BY-NC", "CC BY-ND", "1931"],
        "05-licensing-music-and-fonts": ["desktop license", "webfont", "royalty-free", "sync"],
        "06-accidental-reuse": ["Pinterest", "freelancer", "permission log"],
        "07-trademark-basics-for-series-names": ["trademark", "knockout", "™", "®"],
    }
    for slug, terms in keywords.items():
        text = (DOCS_DIR / f"{slug}.md").read_text(encoding="utf-8").lower()
        for term in terms:
            assert term.lower() in text, f"{slug}: missing '{term}'"


def test_checklist_has_checkable_items() -> None:
    text = (DOCS_DIR / "checklist.md").read_text(encoding="utf-8")
    checks = re.findall(r"^(\s*)- \[ \]", text, flags=re.MULTILINE)
    assert len(checks) >= 10, "checklist should have at least 10 unchecked items"


def test_glossary_has_enough_terms() -> None:
    text = (DOCS_DIR / "glossary.md").read_text(encoding="utf-8")
    entries = re.findall(r"^\*\*(.+?)\.\*\*", text, flags=re.MULTILINE)
    assert len(entries) >= 20, f"glossary should define 20+ terms, found {len(entries)}"


def test_permission_log_sheet_is_valid_csv() -> None:
    path = ROOT / "templates" / "permission-log.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    assert header[0] == "Asset"
    for required in ["Source (page URL)", "License or permission terms", "Expires"]:
        assert required in header
    data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    assert len(data_rows) >= 3, "permission log should include example rows"


def test_permission_log_has_no_real_personal_details() -> None:
    text = (ROOT / "templates" / "permission-log.csv").read_text(encoding="utf-8")
    # All example rows must be obviously fictional placeholders.
    assert "example.com" in text
    assert "Jane Creator" in text
    assert "@" not in text, "template should not contain email addresses"
    assert not re.search(r"\b\d{3}-\d{2}-\d{4}\b", text), "no SSN-like strings"


# ------------------------------------------------------------ hygiene checks


def _files_to_scan() -> list[Path]:
    skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules"}
    files = []
    for path in ROOT.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def test_no_secrets_in_project() -> None:
    for path in _files_to_scan():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            assert not re.search(pattern, text), f"{path.name}: matches secret pattern {pattern}"


def test_no_unused_markdown_links_between_docs() -> None:
    for doc in DOCS_DIR.glob("*.md"):
        for link in re.findall(r"\]\(([^)#\s]+\.md)\)", doc.read_text(encoding="utf-8")):
            assert (DOCS_DIR / link).is_file(), f"{doc.name}: broken .md link {link}"
