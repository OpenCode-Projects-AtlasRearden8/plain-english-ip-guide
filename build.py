#!/usr/bin/env python3
"""Build the Plain-English IP Guide static site from docs/ into site/.

Local-first: no network access, no accounts, no API keys.
Usage:
    python3 build.py           # build site/
    python3 build.py --check   # validate without writing anything
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    import markdown
except ImportError as exc:  # pragma: no cover
    sys.exit(
        "The 'markdown' package is required:  pip install markdown\n"
        f"(import failed: {exc})"
    )

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
SITE_DIR = ROOT / "site"
TEMPLATES_DIR = ROOT / "templates"

SITE_TITLE = "Plain-English IP Guide for Small Creators"
SITE_TAGLINE = (
    "Intellectual property for small creators and tiny LLCs — explained like a "
    "friend would, without the lawyer fog."
)
DISCLAIMER_MARKER = "never legal advice"
COPYRIGHT_LINE = "Copyright (c) 2026 Asdale Dynamics, LLC"

# Every document the site must contain (slug ← filename stem in docs/).
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

MARKDOWN_EXTENSIONS = ["extra", "toc", "sane_lists"]

PAGE_CSS = """/* Plain-English IP Guide — hand-written, dependency-free */
:root {
  --bg: #faf8f4;
  --panel: #ffffff;
  --ink: #2b2620;
  --muted: #6b6055;
  --accent: #2e6e5e;
  --accent-soft: #e3efeb;
  --border: #e5dfd4;
  --warn-bg: #fdf3e3;
  --warn-border: #e4b463;
}
* { box-sizing: border-box; }
html { font-size: 17px; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
  line-height: 1.65;
}
header.site, footer.site {
  padding: 0.6rem 1rem;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
footer.site { border-bottom: none; border-top: 1px solid var(--border); margin-top: 3rem; }
header.site a.home {
  font-weight: bold;
  color: var(--accent);
  text-decoration: none;
}
main {
  max-width: 44rem;
  margin: 0 auto;
  padding: 1.5rem 1rem 0 1rem;
}
h1, h2, h3 { line-height: 1.25; }
h1 { font-size: 1.9rem; margin: 0.5rem 0 1rem; }
h2 { margin-top: 2.2rem; border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
a { color: var(--accent); }
blockquote {
  margin: 1.5rem 0;
  padding: 0.75rem 1rem;
  background: var(--warn-bg);
  border-left: 4px solid var(--warn-border);
  border-radius: 0 6px 6px 0;
}
code, pre { font-family: Consolas, Menlo, monospace; font-size: 0.85em; }
pre { padding: 0.8rem; background: #322c26; color: #f4efe8; border-radius: 8px; overflow-x: auto; }
pre code { color: inherit; background: none; }
code { background: var(--accent-soft); padding: 0.1em 0.35em; border-radius: 4px; }
table { border-collapse: collapse; width: 100%; margin: 1.2rem 0; font-size: 0.95em; }
th, td { border: 1px solid var(--border); padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }
th { background: var(--accent-soft); }
ul { padding-left: 1.3rem; }
li { margin: 0.3rem 0; }
hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
.pagednav { margin-top: 2.5rem; font-size: 0.95em; }
.cards { list-style: none; padding: 0; }
.cards li {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1rem;
  margin: 0.8rem 0;
}
.cards a { font-weight: bold; text-decoration: none; font-size: 1.05em; }
.cards .desc { color: var(--muted); font-size: 0.92em; margin-top: 0.35rem; }
.tagline { color: var(--muted); font-style: italic; }
footer.site p, footer.site small { color: var(--muted); }
"""


class Doc:
    def __init__(self, path: Path):
        self.path = path
        self.slug = path.stem
        raw = path.read_text(encoding="utf-8")
        # Title: first H1 ("# Title") or fallback to the slug.
        m = re.search(r"^# (.+)$", raw, flags=re.MULTILINE)
        self.title = m.group(1).strip() if m else self.slug
        self.html = render_markdown_to_html_fragment(raw)

    def snippet(self) -> str:
        """First non-heading paragraph, stripped of inline markup."""
        text = re.sub(r"<[^>]+>", "", self.html)
        for para in text.split("\n"):
            p = para.strip()
            if p and not p.startswith("Copyright"):
                return (p[:180] + "…") if len(p) > 180 else p
        return ""


def render_markdown_to_html_fragment(md_text: str) -> str:
    html = markdown.markdown(md_text, extensions=MARKDOWN_EXTENSIONS)
    # Links to project-root paths (templates/…) resolve from site/ directly.
    html = html.replace('href="templates/', 'href="')
    # Rewrite links that point at another source markdown doc (x.md -> x.html).
    return re.sub(r'(href=")([^"#]+?)\.md(")', r"\1\2.html\3", html)


def find_md_links(md_text: str) -> list[Path]:
    """Relative .md targets referenced from a doc, resolved against docs/."""
    if isinstance(md_text, str):
        text = md_text
    else:
        text = md_text.read_text(encoding="utf-8")
    targets = []
    for href in re.findall(r"href=\"([^\"]+)\"", text) + re.findall(
        r"\]\(([^)#\s]+\.md)\)", text
    ):
        if href.endswith(".md"):
            targets.append(href)
    return targets


def collect_docs() -> list[Doc]:
    md_files = sorted(p for p in DOCS_DIR.glob("*.md") if p.is_file())
    docs = [Doc(p) for p in md_files]
    slugs = [d.slug for d in docs]
    missing = [s for s in REQUIRED_SLUGS if s not in slugs]
    if missing:
        sys.exit(f"ERROR: missing required doc(s): {', '.join(missing)}")
    return docs


def validate(docs: list[Doc]) -> None:
    problems: list[str] = []

    for doc in docs:
        # 1. Disclaimer check.
        if DISCLAIMER_MARKER not in doc.path.read_text(encoding="utf-8").lower():
            problems.append(f"{doc.path.name}: missing 'never legal advice' disclaimer")

        # 2. Internal cross-links resolve.
        for link in find_md_links(doc.path):
            if link.startswith("templates/"):
                if not (ROOT / link).is_file():
                    problems.append(f"{doc.path.name}: broken internal link -> {link}")
                continue
            target = DOCS_DIR / link
            if not target.is_file():
                problems.append(f"{doc.path.name}: broken internal link -> {link}")

    # 3. Permission log sheets parse with the required first column.
    csv_path = TEMPLATES_DIR / "permission-log.csv"
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0] if rows else []
    if not header or header[0].strip() != "Asset":
        problems.append("templates/permission-log.csv: first column must be 'Asset'")
    if not any(r[0] for r in rows[1:] if r):
        problems.append("templates/permission-log.csv: has no data rows")

    if problems:
        sys.exit("ERRORS:\n" + "\n".join(f" - {p}" for p in problems))


def page(title: str, body: str) -> str:
    today = date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Beginner-friendly intellectual-property guidance for small creators and tiny LLCs, in plain English. Education, never legal advice.">
<title>{title} · {SITE_TITLE}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site"><nav>
  <a class="home" href="index.html">{SITE_TITLE}</a>
</nav></header>
<main>
{body}
<div class="pagednav">
<p><small>Built {today} · plain-english-ip-guide · {COPYRIGHT_LINE} · MIT licensed</small></p>
</div>
</main>
<footer class="site">
<p>This site is an educational resource — <strong>never legal advice</strong>. It does not create an attorney–client relationship. For real disputes and real money, talk to a real IP attorney.</p>
<p><small>{COPYRIGHT_LINE} · Asdale Dynamics, LLC · <a href="https://dylanasdale.github.io">dylanasdale.github.io</a></small></p>
</footer>
</body>
</html>
"""


def index_page(docs: list[Doc]) -> str:
    cards = []
    for doc in docs:
        cards.append(
            f'  <li><a href="{doc.slug}.html">{doc.title}</a>'
            f'<div class="desc">{doc.snippet()}</div></li>'
        )
    body = (
        f"<h1>{SITE_TITLE}</h1>\n"
        f'<p class="tagline">{SITE_TAGLINE}</p>\n'
        "<p>Start with <a href=\"01-copyright-the-moment-you-publish.html\">why you "
        "already own copyright</a>, or jump to the "
        '<a href="checklist.html">pre-publish checklist</a> and the '
        '<a href="permission-log.csv">permission-log sheet</a>. A plain '
        "<a href=\"glossary.html\">glossary</a> has every term the legal pages "
        "throw around.</p>\n<ul class=\"cards\">\n" + "\n".join(cards) + "\n</ul>\n"
        "<blockquote><p><strong>Education, never legal advice.</strong> These "
        "guides are information, not counsel. Nothing in them replaces a real "
        "lawyer, and they never create an attorney–client relationship.</p>"
        "</blockquote>\n"
    )
    return page(SITE_TITLE, body)


def build(check_only: bool) -> None:
    docs = collect_docs()
    validate(docs)

    if check_only:
        print(
            f"check ok: {len(docs)} docs validated "
            f"({', '.join(d.slug for d in docs)})"
        )
        return

    SITE_DIR.mkdir(exist_ok=True)

    shutil.copyfile(TEMPLATES_DIR / "permission-log.csv", SITE_DIR / "permission-log.csv")
    (SITE_DIR / "style.css").write_text(PAGE_CSS, encoding="utf-8")

    for doc in docs:
        (SITE_DIR / f"{doc.slug}.html").write_text(page(doc.title, doc.html), encoding="utf-8")

    (SITE_DIR / "index.html").write_text(index_page(docs), encoding="utf-8")

    count = len(docs) + 2
    print(f"built: {count} files in site/ ({', '.join(d.slug for d in docs)}, index, assets)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without writing")
    build(check_only=parser.parse_args().check)


if __name__ == "__main__":
    main()
