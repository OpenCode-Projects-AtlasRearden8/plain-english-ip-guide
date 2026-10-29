# STATUS.md — plain-english-ip-guide

Last updated: 2026-10-29

## What was built

A complete, self-contained plain-English intellectual property guide for
small creators, indie authors, and tiny LLCs, published as **markdown docs +
a static HTML site built by a local script**. Written in the
Asdale Dynamics, LLC "explain it like a friend would" style: clear, warm,
never condescending, never legal advice.

### Content (source of truth: `docs/`, 9 files)

| Guide | Covers |
| --- | --- |
| 01. Copyright: the moment you publish | Automatic copyright on fixation/publishing; what © notice does; rights you own vs. assets you never bought; platforms, fonts, stock, freelancers |
| 02. What registration actually buys | U.S. registration: right to sue, statutory damages + fees (3-month window), public record, customs; what it does *not* do; costs |
| 03. Fair use and quote myths | Four factors; myth-by-myth decode (word counts, attribution, "public internet", lyrics); U.S. vs fair-dealing differences |
| 04. Public domain & Creative Commons | PD sources, PD cutoff math, PD traps; CC0/BY/BY-SA/BY-NC/BY-ND decoded for images and book covers; choosing CC for your own cover art |
| 05. Licensing music and fonts | Desktop vs webfont font licenses, free-for-personal-use trap, Google Fonts default; composition/master/sync music rights; platform vs multi-platform licenses; royalty-free ≠ copyright-free |
| 06. Accidental reuse of other people's assets | 8 traps ranked by frequency (search images, templates, screenshots, gift art, Canva, AI assets, freelancer IP, borrowed logos) + honest fix playbook (remove, license retroactively, ask, record) |
| 07. Trademark basics for series names | Copyright vs trademark; why series names are trademarkable and single titles are not; one-evening knockout searches; ™ vs ®; registration skim plan |
| checklist.md | Pre-publish asset checklist (10+ yes/no items) |
| glossary.md | 20+ plain-English term definitions with cross-links |

Plus `templates/permission-log.csv` — a permission-log sheet (CSV; one row
per asset: source, license, proof, expiry) with five clearly-fictional
example rows and no personal data.

### Tooling

- `build.py` — stdlib + `markdown` only. Builds `site/` (index + 9 pages +
  style.css + permission-log.csv copy). Rewrites cross-doc `.md` links to
  `.html`, validates internally (`--check` mode: exits non-zero on missing
  docs, broken links, missing disclaimers, malformed permission log).
- `tests/test_build.py` — 17 pytest tests: build succeeds and regenerates
  from a deleted `site/`, every page lists in the index, pages are
  well-formed HTML with resolving links, LICENSE contains the exact line
  `Copyright (c) 2026 Asdale Dynamics, LLC`, README credits the LLC, every
  doc carries the "never legal advice" disclaimer, topic-keyword coverage,
  checklist/glossary/csv structure, and secret-pattern scanning across the
  repo.
- `requirements-dev.txt` — pytest + markdown.

## How to run it

```bash
python3 build.py            # build the static site into site/
python3 build.py --check    # validate without writing (exit 0 = clean)
pytest                      # run the test suite
```

Then open `site/index.html` in a browser. Everything is local: no network
calls, no accounts, no API keys, no personal data. HTML requires no
JavaScript and can be hosted anywhere (e.g. GitHub Pages) after a manual
publish step.

## Verification results (this session)

- `python3 build.py --check` → exit 0, "check ok: 9 docs validated"
- `python3 build.py` → "built: 11 files in site/"
- `pytest` → **17 passed** in ~0.65s
- Fixed during development: stray non-ASCII typographic artifacts in three
  docs, one broken cross-doc link target (`templates/` paths now resolved
  and rewritten by the build), glossary missing its disclaimer footer, and
  a buggy test comparison. All resolved; suite green.
- Applied a critical pass on content: PD cutoff math (Jan 2026 → pre-1931,
  per-year rule "current year minus 96"), CC decode table simplified to
  one-sentence-per-license, music rights split into composition/master/sync,
  trademark title-vs-series distinction.

## Known gaps

- **No lawyer reviewed the text.** All U.S. legal specifics (statutory
  damages ranges, PD terms, registration fees/trademark classes) are stated
  with "always confirm at copyright.gov / USPTO.gov" caveats, but figures
  can change after this guide is published.
- **U.S.-centric** on registration/statutory damages; fair use is covered
  but only contrasted (not fully explained) with U.K./Canadian fair dealing.
- **AI-generated assets** intentionally get only a brief caution in guide 06;
  the law there is unsettled, so the guide says so rather than pretending.
- **No page-to-page "Prev/Next" on index** (guides carry prev/next footers;
  index is a hyperlinked table of contents instead).
- The static site is committed in `site/` so it can be published directly,
  but it is a build artifact — regenerate any time with `python3 build.py`.
