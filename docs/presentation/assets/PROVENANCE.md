# Presentation Assets — Image Sourcing Guide

> **Date:** 2026-07-26
> **Policy:** No third-party photography is committed to this repository.

---

## Design decision

This repository is **public on GitHub**. Committing images with unclear provenance creates
copyright-infringement risk. Therefore:

- **No stock photography, artist renders, or externally-sourced images are committed.**
- Visual impact for slides comes from **self-authored Excalidraw diagrams** (see
  [`../../../docs/architecture/diagrams/`](../../architecture/diagrams/README.md)) and **procedurally generated assets**
  (see [`../../../tools/presentation/assets/`](../../../tools/presentation/assets/)).

---

## Safe options for the presenter's local deck copy

The presenter may drop imagery into their **local working copy** of
`NovaSteel-Oral-Defense.pptx` without committing it to the repo. Acceptable sources:

1. **Customer's own plant photography** (best — most persuasive to a jury; shows real context).
2. **Microsoft-provided brand/industry assets** (e.g., Azure marketing imagery, Microsoft
   Industry stock packs with explicit commercial-use rights).
3. **A licensed stock library** (Shutterstock, Adobe Stock, iStock, etc.) — keep the licence
   receipt alongside the image in a local-only folder. Confirm the licence permits academic
   presentation use.
4. **Creative Commons** images with a confirmed CC-BY or CC0 licence — attribute per the
   licence terms in the speaker notes for that slide.

In all cases: **do not `git add` third-party imagery**. The `.gitignore` entry
`docs/presentation/assets/*.local.*` can be used as a convention for local-only files.

---

## Original diagram assets (committed, no licence risk)

| Asset | Source | Slide support |
|---|---|---|
| `docs/architecture/diagrams/end-to-end-architecture.excalidraw` | Self-authored | Slide 8 (architecture) |
| `docs/architecture/diagrams/deployment-topology.excalidraw` | Self-authored | Slide 17/19 (deployment) |
| `docs/architecture/diagrams/demo-flow.excalidraw` | Self-authored | Slide 20 (demo handoff) |
| `docs/architecture/diagrams/business-value-chain.excalidraw` | Self-authored | **Slides 1–4** (business hook) |
| `tools/presentation/assets/steel-texture.png` | Procedurally generated | Slide backgrounds |
| `tools/presentation/assets/steelworks-hero.png` | Procedurally generated | Slide 1 title |
| `tools/presentation/assets/thermal-map.png` | Procedurally generated | Slide 13 (RUL) |

These carry zero licensing risk and are more defensible in front of a technical jury than
stock photography.

---

## Application screenshots (committed, no licence risk)

`app-guide/screenshots/` holds **37 PNG captures of this repository's own running
application** — 31 route screenshots (one per screen of the analytics microfrontend,
rendered inside the Blazor portal shell) and 6 feature captures (Copilot panel, help
assistant, capacity panel, settings dialog, dark theme, account menu).

| Property | Value |
|---|---|
| Source | `apps/portal-shell` + `apps/analytics-mfe` running locally against the local BFF (`DEMO_MODE=local`) |
| Captured on | 2026-07-28, all 37 re-captured in one pass against the current `main` |
| Viewport | 1680 px wide, full-page capture |
| Data shown | Deterministic **synthetic** fixture data only — every capture carries the "Synthetic demo data — not for operational control" banner |
| Licence risk | **None.** Self-authored capture of first-party software; no third-party imagery, no personal data, no tenant identifiers. |
| Consumed by | [`app-guide/en/README.md`](app-guide/en/README.md) and [`app-guide/fr/LISEZMOI.md`](app-guide/fr/LISEZMOI.md) |

Regeneration instructions are in the guide index (§"Regenerating the screenshots").

---

## Steel Knowledge page artwork (committed as WebP renditions)

The **Steel Knowledge** page of the in-portal AxelorMetal website
(`/{site}/company-website/steel-knowledge`) carries six pieces of process
artwork. Only the optimised WebP renditions in
`apps/portal-shell/wwwroot/media/` are committed; the sources stay local under
`docs/images/` (see [`../../images/README.md`](../../images/README.md)).

| Rendition | Kind | Source | Licence position |
|---|---|---|---|
| `steel-route-blast-furnace` | Illustrated diagram | Generated for this project | No licence risk |
| `steel-route-electric-arc-furnace` | Illustrated diagram | Generated for this project | No licence risk |
| `eaf-process-detail` | Illustrated diagram | Generated for this project | No licence risk |
| `blast-furnace-cutaway` | Schematic | **Supplied by the repository owner** | ⚠️ Confirm before publishing |
| `rolling-mill-stand` | Photograph | **Supplied by the repository owner** | ⚠️ Confirm before publishing |
| `rolling-mill-line` | Photograph | **Supplied by the repository owner** | ⚠️ Confirm before publishing |

> **Action required.** The last three were added on the owner's explicit
> instruction and are the only images in the repository that the "no
> third-party photography" rule above does not already clear. Before this
> repository is published, confirm each one is either owned by AxelorMetal /
> the author, CC0/CC-BY (then attribute here), or covered by a stock licence
> that permits redistribution in a public repository. If a licence cannot be
> confirmed, delete the three `*.webp` renditions and the matching
> `variant="figure"` blocks in `CompanyWebsiteSteelKnowledge.tsx` — the page
> degrades gracefully, because `ProcessDiagram` hides any figure whose asset
> fails to load.

---

## Marp deck diagram renditions (committed as WebP)

The Marp deck (`../slides.md`) carries one process diagram of its own, in the
opening slide *"How a Steel Mill Works"*. It follows the same policy as the
Steel Knowledge artwork above: the ~8 MB PNG source stays local and untracked
under `docs/images/`, and only the optimised WebP rendition is committed.

| Rendition | Kind | Source | Licence position |
|---|---|---|---|
| `diagrams/steel-process-routes.webp` | Illustrated diagram | Generated for this project | No licence risk |
| `diagrams/fabric-architecture-diagram.webp` | Architecture diagram | Supplied by the repository owner for this project | Confirmed project asset |
| `diagrams/fabric-rti-diagram.webp` | Architecture diagram | Supplied by the repository owner for this project | Confirmed project asset |

`../scripts/sync-images.mjs` copies it into the deck's generated `images/`
folder, so `slides.md` references it as `images/steel-process-routes.webp`.
