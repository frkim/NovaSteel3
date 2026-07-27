# Process-diagram source artwork

Illustrated diagrams of the steelmaking process, used on the **Steel Knowledge**
page of the AxelorMetal corporate website inside the portal
(`/{site}/company-website/steel-knowledge`).

| Source file | Web rendition (`stem`) | Subject |
|---|---|---|
| `steel process.png` | `steel-route-blast-furnace` | The integrated route end to end — extraction, blast furnace, basic oxygen furnace, continuous casting, rolling, finished products |
| `steel process with Electric arc furnace.png` | `steel-route-electric-arc-furnace` | The same journey starting from recycled scrap and electricity instead of iron ore and coke |
| `steel process with Electric arc furnace2.png` | `eaf-process-detail` | A ten-step deep dive into the electric arc furnace route |

## Why the sources are not committed

Each source is roughly **8 MB at 2816 × 1536**, so committing all three would add
about 24 MB to the repository permanently. Only the optimised renditions are
tracked — six WebP files totalling about **1.4 MB** in
`apps/portal-shell/wwwroot/media/`.

Keep the sources in this folder locally; `.gitignore` excludes `docs/images/*.png`.

## Regenerating the web renditions

Two renditions are produced per diagram so the browser can pick the cheaper one
on small screens: a `-sm` variant at 900 px and a full variant at 1800 px. The
`ProcessDiagram` component wires them up through `srcSet`/`sizes`.

From the repository root:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
@'
from pathlib import Path
from PIL import Image

SRC = Path("docs/images")
DST = Path("apps/portal-shell/wwwroot/media")
JOBS = [
    ("steel process.png", "steel-route-blast-furnace"),
    ("steel process with Electric arc furnace.png", "steel-route-electric-arc-furnace"),
    ("steel process with Electric arc furnace2.png", "eaf-process-detail"),
]
for src_name, stem in JOBS:
    img = Image.open(SRC / src_name).convert("RGB")
    for width, suffix in ((1800, ""), (900, "-sm")):
        h = round(img.height * width / img.width)
        out = DST / f"{stem}{suffix}.webp"
        img.resize((width, h), Image.LANCZOS).save(out, "WEBP", quality=86, method=6)
        print(f"{out.name} {width}x{h} {out.stat().st_size / 1024:.0f} KB")
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
