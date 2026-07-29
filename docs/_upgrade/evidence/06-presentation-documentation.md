# NovaSteel — Presentation & Documentation Evaluation (Project A vs Project B)

**Evaluator role:** Owner of the *"Clarity of explanation and presentation"* rubric criterion (Azure Master Architect Program — 60-pt rubric, 12 criteria). Fitness assessed for a **1-hour oral defense** to a mixed executive/technical jury.
**Projects compared**
- **PROJECT A** — `D:\work\20260507 - NovaSteel\NovaSteel`
- **PROJECT B** — `D:\work\20260724 - Novasteel 3`
**Method:** direct inspection of every file referenced in the task brief plus wide sampling, with word counts, link probing and consistency spot-checks. Vendored template docs excluded from solution counts as instructed.

---

## 1. Executive verdict

**Project B is materially stronger for a 1-hour oral defense.** It is the only project that ships **an actual PowerPoint file** (`docs\presentation\NovaSteel-Oral-Defense.pptx`, 2.1 MB, 26 slides, 714 text runs — programmatically validated, zero placeholder findings), the only one with an **explicit 60-minute clock (30 slides + 15 demo + 15 FAQ)** with **minute-by-minute speaker notes, rehearsal checkpoints, backup slides, and a written fallback script**, and the only one whose demo runbook is backed by **reproducible evidence artifacts** (66/66 driver checks, deterministic seed `240725`, cached JSON/logs). Its authorial discipline — a codified *"target vs. evidence"* honesty contract carried on every slide, every FAQ entry and the runbook — is exactly the discipline a hard jury rewards.

**Project A is stronger on breadth, business polish, and multilingual reach.** It has a McKinsey-style 16-chapter strategic analysis, a pedagogical 10-chapter "explanation" series (with French translations for the defense), an executive summary that names euro figures, a real live Azure/Fabric environment with URLs, and rich hero imagery (real blast-furnace photos, logo). But it is a **presentation-*plan*, not a presentation**: no .pptx, no speaker notes at slide level, only a 16-slide deck outline scoped for **"30–40 minutes"** — **fundamentally short of the required 60-minute format** — no minute-by-minute rehearsal grid, no explicit fallback ladder for a live demo, and only the copy of the grading rubric in the `10_oral_defense` folder.

**Bottom line for the "Clarity of explanation" criterion (1–5):**
- **Project A: 3.5 / 5** (Satisfactory→Good) — thorough written material and role-adapted language, but the presentation asset itself is a draft outline, oral-defense scaffolding is thin, and the deck plan is under-scoped for a 1-hour defense.
- **Project B: 4.5 / 5** (Good→Excellent) — a defensible, rehearsed, format-correct 60-minute defense pack that a competent presenter could deliver *tomorrow*, with honesty discipline that will survive skeptical questioning. Half-point held back for genre density (very engineering-heavy prose, few hero visuals, no French for a Luxembourg jury).

---

## 2. Documentation inventory

Counts exclude `node_modules`, `.venv`, `.git`, and (for A) the `docs\usecase\0_specs\` speckit template tooling (Spec-Kit is a framework scaffold, not solution documentation).

| Metric | Project A (solution docs) | Project B (solution docs) |
|---|---|---|
| Total `.md` files under `docs\` (solution) | **82** | **21** |
| Total words in `docs\` (solution) | **≈70,300** | **≈80,400** |
| Speckit / tooling docs excluded from above | 38 files / ~39,000 words under `docs\usecase\0_specs\` | none (no vendored template tree) |
| Whole-repo `.md` incl. app/services (excl. `node_modules`) | 146 files / ~880 KB | 76 files / ~340 KB (docs) + ~200 KB (services/infra/apps/artifacts READMEs) |
| **Docs shape** | Many small essay-style files organised in narrative folders | Fewer, much larger reference documents (typical file 3k–8k words) |

**By category (with quality flag: ★ = excellent, ✓ = present/solid, ~ = light, ✗ = missing):**

| Category | Project A | Project B |
|---|---|---|
| Executive summary | ✓ `First_Proposal\00-executive-summary.md` (510 w) + ★ McKinsey `2_mckensey_analysis\00-executive-summary.md` (697 w) — names €24.5M/yr energy, payback <12 mo | ✓ Combined into `docs\README.md` + `oral-defense-and-slide-plan.md`; no dedicated ROI page but explicit refusal to quote a €/hr figure |
| Business case / ROI | ★ `05-cost-estimate.md` (846 w) with build €0.6–1.1M, run €0.3–0.7M/yr, ~€24.5M/yr energy, conservative/base/optimistic + assumptions + sensitivity table | ~ deliberately no euro number; oral-defense-and-slide-plan §"Appendix — Deployment, Capacity & Scale" backup slide & FAQ Q16/Q17 explain *why*: "credible euro figure needs measured pilot CU consumption" — honest but light for a CFO |
| Strategic analysis (McKinsey-style) | ★ 16 files, ~14,900 w, industry context → operating model → risk register | ✗ none in that genre |
| Solution architecture | ✓ `02-solution-architecture.md` (1,460 w) + `02a-fabric-iot-architecture.md` (3,140 w, 7-layer) | ★ `architecture\solution-architecture.md` (**7,131 w**), 12+ ADRs, explicit conflict-resolution table |
| Deployment topology | ~ scattered in 02/02a/03 | ★ `architecture\deployment-topology.md` (**3,706 w**), Sweden Central primary, capacity lifecycle |
| API / contracts | ~ platform README only | ★ `implementation\api-contracts.md` (**5,263 w**) |
| Data / synthetic-data spec | ~ 03-data-and-ai-design (1,133 w) | ★ `data\synthetic-data-and-simulators.md` (**3,999 w**), determinism, physics-first, truth ledger |
| Security & compliance | ✓ `06-security-compliance.md` (881 w) — high-level | ★ `security\security-governance-and-threat-model.md` (**8,167 w**), Prompt Shields, RAI board, EU AI Act gate |
| **Presentation deck (asset)** | ✗ **no `.pptx`**; only `07-presentation-deck.md` (949 w) — a 16-slide *outline* self-scoped to "30–40 min" | ★ **`NovaSteel-Oral-Defense.pptx`** — 2.1 MB, 26 slides (20 primary + 6 FAQ backups), 714 runs, generated deterministically by `tools\presentation\build-deck.js` (1,162 LOC PptxGenJS) |
| **60-minute oral-defense plan** | ✗ absent — the 16-slide plan is 30–40 min, and `10_oral_defense\` contains **only the grading rubric** | ★ `presentation\oral-defense-and-slide-plan.md` (**6,763 w**), minute-by-minute for all 60 minutes with 7 rehearsal checkpoints |
| Speaker notes | ~ short "Notes:" line per slide in the deck outline | ★ 60–150 word speaker notes on every slide + anticipated objections + on-slide fallback |
| FAQ / objection bank | ✓ Q&A section inside `09-links-and-oral-defense.md` — ~12 Q&A, bilingual FR/EN | ★ `presentation\faq.md` (**4,132 w**, ~50+ Q&A across A–M themes; every answer labelled TARGET vs EVIDENCE) |
| Demo script / runbook | ✓ `08-demo-script.md` (617 w) — 5 scenes, ~12 min | ★ `demo\demo-runbook.md` (**2,526 w**), minute-by-minute, cue sheet, 5-level fallback ladder, preflight/day-before |
| Personas / journeys | ~ role list `10-target-audience-roles.md` (503 w) | ★ `personas\personas-and-journeys.md` (**4,554 w**), 8 personas with pains/goals/KPIs/screens/demo-moment mapping |
| UX / dashboard spec | ✗ | ★ `ux\dashboard-specification.md` (**8,140 w**) |
| Operations / runbooks | ~ MANUAL_STEPS.md (698 w) — admin handoff | ★ `operations\operations-and-cost.md` (**4,842 w**) — SLOs, dashboards, on-call, capacity lifecycle |
| Validation evidence | ~ implicit; no repo-wide status report | ★ `validation-report.md` + `artifacts\validation\final\evidence-manifest.json` + `artifacts\demo-validation\rehearsal-report.md` (15 KB) with 66/66 checks logged |
| Explanatory / pedagogical | ★ `09_explaination\` — 10 chapters (~17,000 w) bilingual EN/FR walk-through of Fabric, IoT, governance | ✗ none in that genre |
| MkDocs website / product site | ✓ `docs\usecase\website\` — 14 pages, company/steel/products/compliance | ✗ |
| Business-facing images | ★ 11 real images: logo (4), blast-furnace photos, rolling mills, factory schemas (~3.5 MB) | ~ 3 generated images (steel texture, steelworks hero, thermal-map) |
| Rating rubric copy | ✓ `10_oral_defense\rating_grid.md` | ✗ (not needed — the deck is calibrated to it) |

**Bloat / duplication findings:**
- **Project A** has significant thematic duplication — the "First_Proposal" folder, the "0_preliminary analysis / 2_mckensey_analysis" folder, the "09_explaination" folder and the "1_agentic_work" folder each restate the same four headline outcomes (14/22/21/8) and the same architecture story in different registers. The four folders total ~55,000 words for the same core solution. The `docs\usecase\0_specs\NovaSteel\` tree is Spec-Kit template tooling (correctly excluded as tooling) but adds another 39,000 words of framework text in-repo. **Impact on the defense:** the presenter must decide which document is authoritative, and links between them are inconsistent (`09_explaination` points across relative paths that only work from within `docs\usecase\09_explaination\`).
- **Project B** is close to duplication-free: each doc has a stated *owning workstream*, a header cross-referencing companions, and the README's "Reading paths" table channels each audience into a single entry point. The 21 files are large (avg. ~3,800 w) but do not overlap.

---

## 3. Business-case strength comparison (with actual claimed numbers)

| Claim | Project A | Project B |
|---|---|---|
| Energy per ton target | **−14%** (all files consistent) | **−14%** (baseline **~19.5 → 16.8 GJ/t** — Slide 4, Q1) |
| CO₂ per ton target | **−22%** | **−22%** (baseline **~2.10 → 1.64 t/t**) |
| Furnace warning | **≥21 days** | **≥21 days** (P50 21.0 / P10 16.8 / P90 27.5 as *demo evidence*) |
| High-grade yield | **+8%** | **+8%** (baseline **~90% → 97%**) |
| Energy = share of cost | 35% | 35% |
| Furnace failure cost | ~€8M per event | ~€8M per event |
| Illustrative annual energy benefit | **~€24.5M** at ~1 Mt (Exec Summary + Cost Estimate + McKinsey ES) | intentionally not quoted |
| Illustrative build / run | **€0.6–1.1M build / €0.3–0.7M/yr run** | intentionally not quoted |
| Payback | **<12 months** (base <9, optimistic <6) | intentionally not quoted; "cost drivers only" (FAQ Q16) |
| Fabric SKU | not stated (references "Fabric capacity") | **F2** baseline, F4 on measured contention; **not F64** just for viewer licensing |

**Analysis for the CFO seat of the jury**
- **Project A gives a CFO something to grade.** It commits to an ROI band, an assumptions table (A1–A10), a sensitivity table, and a per-persona role summary. Weakness: figures are all flagged "illustrative demo estimates" and the €24.5M figure is repeated in ≥3 files unchanged, which risks the impression of a headline number that has never been challenged. NPV/IRR are deferred to a workshop — mentioned but not computed.
- **Project B refuses to bluff.** It explicitly says "I won't quote a €/hour figure" (backup slide "Appendix — Deployment, Capacity & Scale", FAQ Q16/Q17) because credible production cost requires measured pilot Fabric CU consumption. That is a **defensible position with a sophisticated CFO** ("this presenter won't invent numbers") but a **weakness with an impatient jury** that wants a bottom line. B compensates with a *savings-ledger mechanism* (Q4) — the way −14% will *become proven* rather than asserted — which is arguably the better strategic answer but requires patient explanation.

**Judgment:** for a rubric that rewards "**adapt to target audience level**", A's approach lands faster with a mixed jury; B's is more architect-mature but demands more talk-time to sell. Given the 60-minute format has budget for it, B's approach is defensible — but a *hybrid* would beat both (see §7 recommended agenda).

---

## 4. Oral-defense readiness comparison

| Asset | Project A | Project B |
|---|---|---|
| **60-min minute-by-minute plan** | ✗ | ★ Yes — every slide has a `Duration` and `Running clock` (e.g. Slide 12: "2:30 · 18:00 → 20:30"), plus §4 checkpoints at 10:00, 18:00, 25:30, 34:15, 35:00, 45:00, 60:00 |
| Deck outline | ✓ 16 slides, self-labeled "30–40 min" — **too short for the format** | ★ 20 primary + 6 FAQ backup slides, timed to 34:45 with 15 s buffer |
| Actual PPT file | ✗ | ★ Generated `NovaSteel-Oral-Defense.pptx` (2.1 MB) with a documented rebuild path (`npm run build`) and a title/backup structure validated by `pptx_titles.log` and `pptx_alignment.log` |
| Speaker notes | ~ one-line "Notes:" per outline slide | ★ 60–150 words per slide, including *anticipated objections* rehearsed aloud (e.g., Slide 9: "Why not Databricks/Snowflake?"; Slide 10: "Contributor is too broad") |
| Executive hook (first 3 min) | ✓ Executive Summary can be read in 60 s; deck outline Slides 1–5 approximately | ★ Slides 1–3 explicitly designed as the hook — title/framing (0:45) → business challenge (1:30) → cost of standing still (1:15) — closing on "doing nothing isn't neutral, it's the most expensive option" |
| Value story with numbers | ★ concrete €24.5M/<12mo payback | ✓ 4 targets with baselines + demo evidence; deliberate refusal of headline € |
| FAQ / hard-question bank | ✓ ~12 Q&A bilingual | ★ **50+ Q&A** grouped in themes A–M (business value, Fabric centrality, alternatives, capacity, regions, RAI, security, OT realism, synthetic data, models, deployment, scalability, **limitations**) |
| Demo script | ✓ 5-scene, ~12 min | ★ 15-min, 15 rows minute-by-minute, cue sheet (RUL 21.0/16.8/27.5, work order `WO-DEMO-LUX-1042`), **5-level fallback ladder** (live cloud → local replay → cached interactive → recorded flow → static proof pack), never diagnose > 10 s on-screen |
| Backup / edge-case slides | ✗ appendix list only (A1–A5 titles) | ★ 6 dedicated FAQ backup slides in the built PPTX (`BACKUP 1..6`) |
| Rehearsal evidence | ✗ | ★ `artifacts\demo-validation\` — 66/66 driver checks, 2 independent generations reproducing bit-for-bit, HTTP snapshots for every DM-1…DM-6 step, rehearsal report (15.4 KB) |
| Live demo environment | ✓ real Fabric workspace URL + tenant GUID published (`09-links-and-oral-defense.md`) — impressive **and slightly risky** (see §5) | ~ local deterministic demo only ("no cloud tenant deployment") — presenter runs offline; less impressive to jury who want cloud but zero live-cloud risk |
| Bilingual FR/EN | ★ 09-links-and-oral-defense.md is bilingual; `usecase_FR.md` present | ✗ English only |
| Adapts to audience mixed level | ★ 09_explaination series is written for a non-expert reader; McKinsey is written for an exec | ✓ within a single document the same fact is stated for an executive (bullet), a technical reviewer (speaker notes) and for a challenger (anticipated objection) |
| Timing discipline in doc | ✗ | ★ "if a checkpoint slips by 30 s, cut depth (not honesty) from the next section" — real presenter engineering |

**Fitness for a 1-hour defense to a mixed jury:**
- **Project A** requires the presenter to build the deck from the outline, add 20+ minutes of content to reach 60 min, invent minute-by-minute pacing, invent a fallback ladder, and pick which of four overlapping story registers to use on the day. The strategic thinking is there; the *deliverable* is not.
- **Project B** ships a defense pack a competent presenter could rehearse against tonight and defend tomorrow. Its weakness is that it is engineering-tone dense — the same fact stated three ways per slide is thorough but not sparkling; a Luxembourg jury will notice the missing French.

---

## 5. Diagram & visual asset comparison

| Asset type | Project A | Project B |
|---|---|---|
| Mermaid blocks in `docs\` (excluding tooling) | **29** across 19 files | **11** across 3 files |
| Excalidraw source diagrams | **1** (`fabric-iot-architecture.excalidraw`, 92 KB) | **3** (`end-to-end-architecture.excalidraw` 85 KB, `deployment-topology.excalidraw` 76 KB, `demo-flow.excalidraw` 58 KB) — each with a `README.md` describing what it depicts |
| PNG/JPG (business & content) | **11 hero images** (4 logo files, 2 real blast-furnace photos, 2 rolling-mill photos, 2 schema PNGs, 1 fabric-iot-architecture PNG) — total ~3.6 MB — real production-plant photography lifts the deck | **3 generated PNGs** (steel-texture, steelworks-hero, thermal-map) — total ~860 KB — assets are procedurally generated by `generate_assets.py`; adequate but visually less rich |
| Drawio | 0 | 0 |
| **PPTX** | **0** | **1 × 2.1 MB, 26 slides, validated** |
| PDF | 0 | 0 |
| Diagram *coverage* | Broad — a diagram for almost every doc; Mermaid in every McKinsey chapter | Concentrated — architecture, deployment, UX, demo flow; each intentionally the primary teaching visual for its chapter |
| Diagram *editability* | Editable (Mermaid text, one Excalidraw) | Editable (Mermaid text, three Excalidraw with a README) |
| Slide visual quality | ✗ no rendered artefact to judge | Rendered by PptxGenJS (native shapes) — sober industrial palette (carbon/rust/steel/amber), Bahnschrift+Aptos, per-slide unique visual — style code is in `build-deck.js` §palette |

**Judgment:** A wins on *photography and volume of diagrams*, which matters for executive impact. B wins on *diagrams-that-teach-a-specific-architecture-point* and, decisively, on *having an actual rendered deck*. If a jury opens the folder, only B has something to open.

---

## 6. Consistency, credibility & broken-link findings

### Project A
- **Headline numbers are consistent** across the 30+ files that quote 14/22/21/8. That is a genuine strength — no contradictions found in sampling.
- **Scope mismatch: the presentation deck is scoped for the wrong duration.** `07-presentation-deck.md` line 8: *"Target length: ~16 slides for a crisp 30–40 minute executive session"*. The Master Architect Program defense is **60 minutes**. There is no companion "long defense" plan and no minute-by-minute timing.
- **`10_oral_defense\` contains only the rubric.** There is no defense-specific narrative in the folder its name promises (`rating_grid.md` only). A jury opening the "oral defense" folder finds their own rubric, nothing else.
- **Tenant IDs exposed in a committed doc.** `docs\usecase\09_explaination\09-links-and-oral-defense.md` publishes Fabric workspace GUID, subscription GUID, and tenant GUID (§9.1). Verified real. This is **fine for a personal demo repo** but a habit worth flagging — it would fail a "presentation hygiene" review at a Microsoft customer.
- **Reference-file link probing** (sampled 5 outbound links from `09-links-and-oral-defense.md`): `First_Proposal\00-executive-summary.md` ✓, `technical\architecture-principles.md` ✓, `platform\README.md` ✓, `infrastructure\README.md` ✓, `0_specs\NovaSteel\.specify\memory\constitution.md` ✓, `business\images\fabric-iot-architecture.excalidraw` ✓ — **all resolve.** Internal-link hygiene is good.
- **Demo script (`08-demo-script.md`) references a "recorded screen capture" fallback but no file is committed** — pure narrative fallback, no artifact behind it.
- **"AI advises, metallurgists decide" claim is present and consistent** — a nice honesty note, but Project A does *not* have B's explicit **TARGET vs EVIDENCE** discipline: numbers like "21-day warning" and "+8% yield" are stated the same way whether they are aspirations or measurements. A challenging jury will press on this.

### Project B
- **`docs\presentation\NovaSteel-Oral-Defense.pptx` exists and is validated** (see `artifacts\demo-validation\logs\pptx_validate.log` — "PPTX package validation passed (26 slides, 714 text runs)").
- **Consistency between slide plan, FAQ, runbook and validation evidence is very high.** RUL numbers (P10=16.8, P50=21.0, P90=27.5, risk 0.87), work order id `WO-DEMO-LUX-1042`, seed `240725`, F2 SKU, Sweden Central, ADR-001…ADR-009 are quoted identically across four documents.
- **Explicit "target vs evidence" discipline** is applied to every quantitative claim — Slide 4 stamps 🎯 TARGET on each of 14/22/21/8; Slide 12 stamps 🔬 EVIDENCE on the RUL fan chart; the FAQ opens with the same legend. This is a rubric-level "adapt to target audience" strength.
- **Under-sold to a CFO:** deliberately no €/hr, no NPV, no payback. FAQ Q16/Q17 explains the refusal (professional), but a CFO who wanted a slide with a number will find only categories. Suggest a *bridge slide* in future revs (see §7 fixes for B).
- **No French** despite Luxembourg HQ / EU jury — a small but real localization gap.
- **Very engineering-toned** — long paragraphs, high information density; strong for the technical/security seats, less warm for the COO/Executive seat.
- **Broken-link check:** `docs\presentation\NovaSteel-Oral-Defense.pptx` (referenced from `oral-defense-and-slide-plan.md` and `docs\README.md`) — ✓ exists. `artifacts\demo-validation\rehearsal-report.md` ✓. `artifacts\validation\final\evidence-manifest.json` ✓. All sampled internal links resolve.
- **Determinism claim is verifiable.** `rerun_determinism.log` and `genA-hashes.txt`/`genB-hashes.txt` allow the jury to challenge "did you really regenerate bit-for-bit" and B can answer *"open this file"*.

**Overall credibility:** B > A. B is auditable end-to-end; A has more evidence-of-thinking but less evidence-of-testing.

---

## 7. Proposed score on "Clarity of explanation and presentation" (1–5)

Rubric text (Excellent = 5): *"Clear, concise, and thorough presentation. Demonstrates ability to adapt to target audience level."*

| Project | Score | Justification |
|---|---|---|
| **PROJECT A** | **3.5 / 5** (Satisfactory→Good) | **Thorough**: 16 chapters of McKinsey analysis + 10 chapters of pedagogical FR/EN explanation is genuinely rare. **Adapts to audience**: per-persona role summaries, bilingual FR, MkDocs public site. **But**: not concise (55k+ words across 4 overlapping registers for the same story), and the *presentation itself* is a 16-slide outline scoped to 30–40 min — under-length for a 60-min defense, no `.pptx`, no minute-by-minute plan, no fallback ladder, no rehearsal evidence, `10_oral_defense\` contains only the rubric. A jury would give credit for the strategic thinking and penalize for the missing deliverable. |
| **PROJECT B** | **4.5 / 5** (Good→Excellent) | **Clear**: TARGET vs EVIDENCE legend on every claim, "one idea per slide" design principle, a Reading Paths table in `docs\README.md`. **Concise**: 21 large docs, no duplication, each with a stated owner. **Thorough**: the *only* project with a validated 60-min plan, generated PPTX, 26 slides, 50+ FAQ, 15-min runbook with 5-level fallback, and reproducible rehearsal evidence. **Adapts**: executive bullet + technical speaker note + rehearsed objection on the same slide. **Half-point held back**: engineering-heavy tone, few hero visuals, English only, no €/NPV headline number for a CFO seat, and the density will feel dry to a COO. |

---

## 8. Top 5 fixes for each project

### Project A — top 5 (in order of jury impact)
1. **Build the actual 60-minute deck (as a `.pptx`)** — expand the 16-slide outline into a 22–26 slide 60-minute deck, add per-slide speaker notes (100–150 w each), and check it into `docs\usecase\10_oral_defense\NovaSteel-Oral-Defense.pptx`. Consider Marp or PptxGenJS to make it regenerable from Markdown, as B does.
2. **Write a minute-by-minute 60-min plan** with running-clock times and 4–6 rehearsal checkpoints; put it in `docs\usecase\10_oral_defense\oral-defense-plan.md`. Currently that folder contains only a copy of the grading rubric.
3. **Adopt an explicit "target vs evidence" (or "aspiration vs measurement") label discipline** and apply it to every quantitative claim (14/22/21/8, €24.5M, <12-month payback). Today the same visual style is used for aspirations and measurements — a hostile juror will drive a wedge there.
4. **Prune the 4 overlapping narratives (First_Proposal / mckensey_analysis / 09_explaination / 1_agentic_work) into a single canonical README with pointers**, or state upfront which folder is authoritative. Add a "Reading paths" table like B's.
5. **Add a written fallback ladder for the live demo and commit the fallback assets** (screen recording, cached JSON, static screenshots). The current `08-demo-script.md` mentions "Fallback: recorded screen capture" but no file exists — a network failure on the day would leave the presenter improvising. **Bonus:** rotate the exposed tenant/subscription/workspace GUIDs before public distribution.

### Project B — top 5 (in order of jury impact)
1. **Add one CFO bridge slide** with an *illustrative* build/run/benefit band (mirroring A's cost estimate) — explicitly labelled 🎯 TARGET with a stated assumption row and a sensitivity range. The current refusal to quote a number is defensible but leaves the CFO seat unfed for 60 minutes. Anchor it with the same discipline used elsewhere ("baseline X → Y with assumption Z").
2. **Add a French-language executive summary and glossary** (1–2 pages) for the Luxembourg jury. The rest can stay English but the exec preamble in FR is a small effort with high adaptation-to-audience payoff for the rubric.
3. **Add 2–3 hero visuals** — a real blast-furnace photo (or a permissive stock image), a Fabric-centered architecture rendered to PNG at high resolution, and a Sankey-style value flow — to relieve the slide density on Slides 1–8. The current `steelworks-hero.png` is procedurally generated and reads a bit synthetic.
4. **Compress the "one idea per slide" principle harder on Slides 8–10** (Architecture Map / ADR / Trustworthy Data). At 6:45 of speech across three slides they are the densest patch of the 35 minutes; a rehearsal will show this. Consider one animated build-up on Slide 8 rather than three consecutive dense slides.
5. **Ship a short "presenter's rehearsal card"** (1 page) that lists the 7 checkpoint clocks, the 5-level fallback ladder short-form, and the 4 headline numbers with baselines. Currently these live inside a 6,763-word plan; a physical card lowers demo-day risk.

---

## 9. Recommended 60-minute defense agenda (based on the stronger project — Project B)

The agenda below is Project B's structure with two Project-A-inspired additions (a CFO number-slide and a French-language opener sentence) — presented as a ready-to-use plan.

| Clock | Segment | What happens | Key artifact |
|---|---|---|---|
| **00:00 – 00:45** | S1 Title & framing (bilingual EN/FR opener) | Set identity + honesty contract | Slide 1 |
| **00:45 – 03:30** | S2–S3 Business challenge & cost of standing still | Executive hook: 35% energy, €8M failures, retiring experts, ETS | Slides 2–3 |
| **03:30 – 05:15** | S4 Four targets with baselines | 🎯 label; falsifiable | Slide 4 |
| **05:15 – 08:30** | S5–S6 One-platform overview + non-negotiable guardrails | "Decision support, not a control system"; EU-only; no standing secrets | Slides 5–6 |
| **08:30 – 10:00** | S7 8 personas → dashboard map | Set up the demo tabs | Slide 7 |
| **10:00 – 14:45** | S8–S9 Architecture map + why Fabric is the centre (ADR-001/002) | Panel probe expected here | Slides 8–9 |
| **14:45 – 18:00** | S10–S11 OT-signal-to-trust + 4 AI capabilities frame | Bronze/silver/gold + quarantine; "Python decides, Foundry explains" | Slides 10–11 |
| **18:00 – 25:30** | S12–S15 Deep dives: RUL / Energy / Quality / Knowledge | Each with 🔬 EVIDENCE band + guardrail | Slides 12–15 |
| **25:30 – 30:45** | S16–S17 Responsible AI + Security & residency | Prompt Shields, RAI board, EU AI Act, four-plane identity | Slides 16–17 |
| **30:45 – 32:15** | S18 Synthetic data & OT realism | Determinism, physics-first, truth ledger | Slide 18 |
| **32:15 – 34:15** | S19 Compliance (AI Act / ETS / IEC 62443 / NIS2 / GDPR) | Regulation-to-control map; append-only audit chain, emission lineage, outbound-only DMZ, 24 h/72 h path; open gates named. Capacity/cost + CFO illustrative band moved to the "Appendix — Deployment, Capacity & Scale" backup slide | Slide 19 |
| **34:15 – 35:00** | S20 Demo handoff (buffer) | Timer starts, banner up | Slide 20 |
| **35:00 – 45:00** | **Live 10-minute demo** — 6 persona moments DM-1…DM-6 | Deterministic, seed `240725`, 60× clock, 5-level fallback ready | `demo-runbook.md` + `drive_demo.py` |
| **45:00 – 60:00** | Moderated FAQ (target ≥ 8–10 questions) | Themes A–M; open with a "limitations" answer for skeptic-priming | `faq.md` + 6 BACKUP slides |

**Rehearsal gates:** CP-1 10:00 · CP-2 18:00 · CP-3 25:30 · CP-4 34:15 · CP-5 35:00 · CP-6 45:00 · CP-7 60:00.
**Fallback ladder (memorize):** live cloud → local deterministic replay → cached interactive → recorded flow → static proof pack. Never diagnose > 10 seconds on-screen.

---

## Appendix A — Selected citations

- Project A executive summary: `docs\usecase\First_Proposal\00-executive-summary.md:32-40` (four targets), `05-cost-estimate.md:63-84` (€24.5M/yr, payback), `07-presentation-deck.md:8` (self-labelled 30–40 min).
- Project A oral defense folder: `docs\usecase\10_oral_defense\rating_grid.md` — only file in the folder.
- Project A tenant GUIDs published: `docs\usecase\09_explaination\09-links-and-oral-defense.md:12-24`.
- Project B deck plan: `docs\presentation\oral-defense-and-slide-plan.md:14-20` (60-min segments), `:45` (timing envelope), `:369-381` (rehearsal checkpoints).
- Project B PPTX validation: `artifacts\demo-validation\logs\pptx_validate.log` ("PPTX package validation passed (26 slides, 714 text runs).") and `pptx_alignment.log` (10 PASS transitions).
- Project B honesty contract: `docs\presentation\oral-defense-and-slide-plan.md:22-29` (TARGET/EVIDENCE/SOURCE CUE/FALLBACK legend).
- Project B rehearsal evidence: `artifacts\demo-validation\rehearsal-report.md`, `artifacts\demo-validation\http\_summary.json`, `artifacts\validation\final\evidence-manifest.json`.
- Project B FAQ scale: `docs\presentation\faq.md` — 4,132 words, ~50 Q&A across 13 themes.
- Project B build tool: `tools\presentation\build-deck.js` (1,162 LOC, PptxGenJS), `tools\presentation\package.json`, `tools\presentation\README.md`.

---
*Report author: presentation-and-documentation evaluator role for the Azure Master Architect Program jury. All quantitative claims verified by direct file inspection at 2026-07-25.*
