# NovaSteel presentation (Marp)

Fully autonomous build of the NovaSteel oral-defense deck from a single Markdown
source, using [Marp](https://marp.app/). One source file produces the web deck,
the PDF (with and without speaker notes) and the PowerPoint package.

| File | Role |
|---|---|
| `slides.md` | The deck source. 22 timed slides for a 35-minute talk plus 13 FAQ/appendix backup slides. |
| `theme.css` | The `novasteel` Marp theme (brand palette, card grid, split layout, chips). |
| `marp.config.mjs` | Renders emoji as text so the build never depends on the Twemoji CDN. |
| `scripts/sync-images.mjs` | Copies brand assets and UI screenshots into `images/` from their canonical repository locations. |
| `scripts/format-pptx-notes.mjs` | Rewrites the Marp `.pptx` so each speaker-note line becomes its own PowerPoint paragraph. |
| `scripts/strip-notes.mjs` | Writes `slides.pages.md` without speaker notes for the public GitHub Pages deck. |
| `scripts/verify-build.mjs` | Checks that HTML, both PDFs and the PPTX carry every slide and its speaker notes. |
| `dist/` | Build output (git-ignored). |
| `images/` | Build output (git-ignored) — regenerate with `npm run images`. |

## Build locally

```bash
cd presentation
npm install --ignore-scripts   # resolves through the protected npm feed configured in /.npmrc
npm run build                  # HTML + PDF + PDF with notes + PPTX into dist/
```

Individual targets: `npm run html`, `npm run pdf`, `npm run pdf-notes`, `npm run pptx`, `npm run verify`.
`npm run dev` starts the Marp preview server with live reload.

PDF and PPTX conversion needs a Chromium-based browser on the machine (Marp uses it
as the rendering engine). Point `CHROME_PATH` at the executable if it is not on the
default search path.

Package resolution uses the Microsoft-protected npm feed declared in the repository
root [`.npmrc`](../.npmrc); never add a public registry here.

## Build in CI

[`.github/workflows/presentation.yml`](../.github/workflows/presentation.yml) rebuilds
the deck on every push and pull request that touches `presentation/`, and uploads the
whole build output — `index.html`, `NovaSteel-Oral-Defense.pdf`,
`NovaSteel-Oral-Defense-notes.pdf` and `NovaSteel-Oral-Defense.pptx` — as the
`novasteel-presentation-<run id>` workflow artifact (90-day retention). The run summary
lists each file with its size. On `main` it also publishes the HTML deck to GitHub Pages
at the site root — <https://frkim.github.io/NovaSteel3/> — with the PDF and PPTX next to
it (`NovaSteel-Oral-Defense.pdf`, `NovaSteel-Oral-Defense.pptx`); the older `/deck/` URL
redirects there. The Pages copy is generated from a stripped `slides.pages.md` so speaker
notes are never published on the web.

Publishing requires GitHub Pages to be enabled once, by a repository admin, under
**Settings → Pages → Source: GitHub Actions**. The workflow's `GITHUB_TOKEN` cannot
create the Pages site itself, so while Pages is disabled the `Configure Pages` step
only emits a warning: the deck is still built, verified and uploaded as workflow
artifacts, and the `github-pages-deploy` job is skipped.

## Editing rules

- Every content slide carries exactly one speaker note comment that starts with a
  timing marker, e.g. `<!-- ⏱ 1:30 · … -->`. The markers are the timing budget:
  `tests/presentation/test_marp_deck.py` fails the build if the 22 main slides do
  not add up to a 35-minute talk. Backup and appendix slides carry `⏱ 0:00` so they
  stay outside the speaking budget. The defense clock is 35 min slides + 10 min live
  demo + 15 min Q&A.
- Keep the honesty contract of the project: 🎯 TARGET (projected outcome) versus
  🔬 EVIDENCE (reproducible synthetic-scenario result), and the persistent footer
  `AI advises, humans decide`
- Only reference images that `scripts/sync-images.mjs` provides; the test suite
  checks every `images/…` reference against that manifest.
- The title slide's logo bar reads `docs/images/logo/NovaSteel Logo.png`,
  `docs/images/logo/ama_logo.png` (falling back to the tracked
  `docs/AxelorMetal-web/logo/AxelorMetal_logo_full_alpha.png`) and
  `docs/images/logo/microsoft_logo.png`. The Microsoft mark is a trademark asset the
  repository does not ship: drop the file at that path and the next `npm run images`
  picks it up, otherwise the slot removes itself and the bar closes up.
- [`docs/presentation/oral-defense-and-slide-plan.md`](../docs/presentation/oral-defense-and-slide-plan.md)
  stays the authoritative narrative script; `slides.md` is its rendered deck.
  The PptxGenJS deck under [`tools/presentation`](../tools/presentation/README.md)
  remains the previously delivered `docs/presentation/NovaSteel-Oral-Defense.pptx`.
