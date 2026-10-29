# Plain-English IP Guide for Small Creators

A beginner-friendly guide to intellectual property for small creators, indie
authors, and tiny LLCs — written the way a friend would explain it over coffee:
plain English, step by step, never condescending, and no lawyer fog.

Built by **Asdale Dynamics, LLC** as part of Dylan Asdale's
["explain it like a friend would"](https://dylanasdale.github.io) series.

## What's inside

| Topic | Guide |
| --- | --- |
| Copyright happens the moment you publish | [docs/01-copyright-the-moment-you-publish.md](docs/01-copyright-the-moment-you-publish.md) |
| What registration actually buys | [docs/02-what-registration-buys.md](docs/02-what-registration-buys.md) |
| Fair use and quote myths | [docs/03-fair-use-and-quote-myths.md](docs/03-fair-use-and-quote-myths.md) |
| Public domain & Creative Commons decoded (images, covers) | [docs/04-public-domain-and-creative-commons.md](docs/04-public-domain-and-creative-commons.md) |
| Licensing music and fonts for LLC posts | [docs/05-licensing-music-and-fonts.md](docs/05-licensing-music-and-fonts.md) |
| Accidentally reusing other people's assets | [docs/06-accidental-reuse.md](docs/06-accidental-reuse.md) |
| Trademark basics for series names | [docs/07-trademark-basics-for-series-names.md](docs/07-trademark-basics-for-series-names.md) |
| Pre-publish asset checklist | [docs/checklist.md](docs/checklist.md) |
| Glossary | [docs/glossary.md](docs/glossary.md) |
| Permission-log sheet | [templates/permission-log.csv](templates/permission-log.csv) |

## How to build and test (local-first)

Everything runs on your machine. No network calls, no accounts, no API keys.

```bash
# Build the static HTML site into site/
python3 build.py

# Verify the build without writing files (exit code 0 = all good)
python3 build.py --check

# Run the test suite (requires pytest; see requirements-dev.txt)
pytest
```

Open `site/index.html` in any browser to read the guide. The built site is
plain static HTML — it can be pushed anywhere (including
`dylanasdale.github.io`) without a runtime, a server, or JavaScript.

## What the build produces

```
site/
  index.html                                # landing page + table of contents
  01-copyright-the-moment-you-publish.html  # one page per guide
  ...
  checklist.html
  glossary.html
  permission-log.csv                        # copy of the permission-log sheet
  style.css
```

Every page cross-links to the others, carries the same warm-but-clear tone,
and ends with the "this is education, never legal advice" disclaimer.

## The permission log

Fill in `templates/permission-log.csv` as you use assets: type in the asset,
where it came from, what license or permission you have, and when it expires.
One row per asset. It is a plain CSV so it opens in any spreadsheet app and
never requires giving data to a third-party site.

## Testing approach

`tests/test_build.py` runs the build and then verifies, among other things:

- the build completes and produces every expected page
- the LICENSE file contains the exact required copyright line
- the README credits the right entity without naming a person in legal files
- every internal link in the docs resolves to a real file
- each guide carries the education-only disclaimer
- the permission log and glossary parse and have their required parts
- no committed file contains anything shaped like a secret or API key

## Project layout

```
docs/       # the markdown guides (source of truth)
templates/  # permission-log.csv sheet
site/       # generated static HTML (rebuild any time with build.py)
tests/      # pytest suite
build.py    # local build + check script (stdlib + markdown only)
```

## What this project is

This project is an **educational resource**. It is written in everyday
language on purpose. It is **never legal advice**, it is not a lawyer, and
nothing here creates an attorney–client relationship. When real money or real
disputes are on the line, talk to a real IP attorney.

MIT licensed. Copyright (c) 2026 Asdale Dynamics, LLC.
