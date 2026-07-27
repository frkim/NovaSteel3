# Process-diagram source artwork

Illustrated diagrams and photographs of the steelmaking process, used on the
**Steel Knowledge** page of the AxelorMetal corporate website inside the portal
(`/{site}/company-website/steel-knowledge`).

## Full-width diagrams

Rendered by `ProcessDiagram` at its default `full` width, because their small
in-artwork labels need the whole content column.

| Source file | Web rendition (`stem`) | Subject |
|---|---|---|
| `steel process.png` | `steel-route-blast-furnace` | The integrated route end to end — extraction, blast furnace, basic oxygen furnace, continuous casting, rolling, finished products |
| `steel process with Electric arc furnace.png` | `steel-route-electric-arc-furnace` | The same journey starting from recycled scrap and electricity instead of iron ore and coke |
| `steel process with Electric arc furnace2.png` | `eaf-process-detail` | A ten-step deep dive into the electric arc furnace route |

## Uniform figures

Rendered by `ProcessDiagram variant="figure"`, which puts every one of them in
an identical 460 px, 4:3 frame (`FIGURE_WIDTH` / `FIGURE_RATIO` in
`CompanyWebsiteDiagram.tsx`) so they line up with one another instead of each
claiming a different slice of the page. Only one rendition is produced per
figure — the displayed frame never exceeds 460 CSS px, so a `-sm` variant would
never be selected.

| Source file | Web rendition (`stem`) | Subject | Placement |
|---|---|---|---|
| `Blast_furnace_schema2.png` | `blast-furnace-cutaway` | Labelled section of a blast furnace with its 600 → 1,600 °C gradient | "Making Iron & Steel" → *The blast furnace route* |
| `rolling_mils_01.png` | `rolling-mill-stand` | Close-up of one rolling stand with strip passing between the work rolls | "Shaping Metals" → *Rolling in practice* |
| `rolling_mils_02.jpeg` | `rolling-mill-line` | Plant-scale hot rolling line with glowing bar between the stands | "Shaping Metals" → *Rolling in practice* |

> **Licence check outstanding.** The three figure sources were supplied by the
> repository owner rather than authored in-repo. Confirm their licence permits
> redistribution before this repository is made public — see
> [`../presentation/assets/PROVENANCE.md`](../presentation/assets/PROVENANCE.md).

## Why the sources are not committed

Each full-width source is roughly **8 MB at 2816 × 1536**, so committing all
three would add about 24 MB to the repository permanently. Only the optimised
renditions are tracked — nine WebP files totalling about **1.6 MB** in
`apps/portal-shell/wwwroot/media/`.

Keep the sources in this folder locally; `.gitignore` excludes `docs/images/*.png`,
`*.jpg` and `*.jpeg` under the same policy. The remaining photographic sources
(`steel-plant-with-blast-furnace.jpg`, `blast_furnace-schema.png`,
`blast_furnace-schema3.jpg`) are held here as raw material for future website
work and are not yet referenced by any page.

### What *is* tracked here

`docs/images/logo/` holds the NovaSteel wordmark and mark sources (Paint.NET
`.pdn` plus exported PNGs, ~1.3 MB total). These are committed, matching the
AxelorMetal logo sources in `docs/AxelorMetal-web/logo/`, because they are small
and are the provenance for the tracked shell assets in
`apps/portal-shell/wwwroot/brand/` (`novasteel-mark.png`,
`novasteel-mark-dark.png`, `axelormetal-*.png`).

## Regenerating the web renditions

Two renditions are produced per **full-width diagram** so the browser can pick
the cheaper one on small screens: a `-sm` variant at 900 px and a full variant
at 1800 px. The `ProcessDiagram` component wires them up through
`srcSet`/`sizes`. **Figures** get a single rendition, capped at the source width
so nothing is upscaled.

From the repository root:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
@'
from pathlib import Path
from PIL import Image

SRC = Path("docs/images")
DST = Path("apps/portal-shell/wwwroot/media")

DIAGRAMS = [
    ("steel process.png", "steel-route-blast-furnace"),
    ("steel process with Electric arc furnace.png", "steel-route-electric-arc-furnace"),
    ("steel process with Electric arc furnace2.png", "eaf-process-detail"),
]
FIGURES = [
    ("Blast_furnace_schema2.png", "blast-furnace-cutaway", 1160),
    ("rolling_mils_01.png", "rolling-mill-stand", 1200),
    ("rolling_mils_02.jpeg", "rolling-mill-line", 1200),
]

def save(img, out, width):
    h = round(img.height * width / img.width)
    img.resize((width, h), Image.LANCZOS).save(out, "WEBP", quality=86, method=6)
    print(f"{out.name} {width}x{h} {out.stat().st_size / 1024:.0f} KB")

for src_name, stem in DIAGRAMS:
    img = Image.open(SRC / src_name).convert("RGB")
    for width, suffix in ((1800, ""), (900, "-sm")):
        save(img, DST / f"{stem}{suffix}.webp", width)

for src_name, stem, max_width in FIGURES:
    img = Image.open(SRC / src_name).convert("RGB")
    save(img, DST / f"{stem}.webp", min(max_width, img.width))
'@ | .\services\bff-api\.venv\Scripts\python.exe -
```

Pillow is already present in the `bff-api` virtual environment. If it needs
reinstalling, use the approved Microsoft package feed:

```powershell
.\services\bff-api\.venv\Scripts\pip.exe install `
  --index-url https://packagefeedproxy.microsoft.io/pypi/simple pillow
```

Quality 86 was chosen as the point where the small in-diagram labels stay
legible at 400 % lightbox zoom while each file stays under 400 KB.
