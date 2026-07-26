# Presentation Assets — Image Sourcing Guide

> **Date:** 2026-07-26
> **Policy:** No third-party photography is committed to this repository.

---

## Design decision

This repository is **public on GitHub**. Committing images with unclear provenance creates
copyright-infringement risk. Therefore:

- **No stock photography, artist renders, or externally-sourced images are committed.**
- Visual impact for slides comes from **self-authored Excalidraw diagrams** (see
  [`../../../docs/diagrams/`](../../diagrams/README.md)) and **procedurally generated assets**
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
| `docs/diagrams/end-to-end-architecture.excalidraw` | Self-authored | Slide 8 (architecture) |
| `docs/diagrams/deployment-topology.excalidraw` | Self-authored | Slide 17/19 (deployment) |
| `docs/diagrams/demo-flow.excalidraw` | Self-authored | Slide 20 (demo handoff) |
| `docs/diagrams/business-value-chain.excalidraw` | Self-authored | **Slides 1–4** (business hook) |
| `tools/presentation/assets/steel-texture.png` | Procedurally generated | Slide backgrounds |
| `tools/presentation/assets/steelworks-hero.png` | Procedurally generated | Slide 1 title |
| `tools/presentation/assets/thermal-map.png` | Procedurally generated | Slide 12 (RUL) |

These carry zero licensing risk and are more defensible in front of a technical jury than
stock photography.
