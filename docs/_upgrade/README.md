# NovaSteel — Comparative Analysis & Oral Defense Decision Pack

Deep comparison of two competing implementations of the NovaSteel use case, scored against the
official jury rating grid, with a final recommendation ahead of the **1-hour oral defense**.

---

## 🏁 The answer

> ## Keep **Project B** — `D:\work\20260724 - Novasteel 3`
>
> **B scores 48.5 / 60 (Grade B). A scores 34.5 / 60 (Grade D/F).**
> B wins or ties **11 of the 12 rubric criteria**.
>
> Then transplant Project A's three genuine algorithmic assets into it — the **PuLP MILP
> optimizer**, the **physics-informed RUL regression**, and the **live GPT-5 grounded RAG**.
> That takes B to a realistic **56–58 / 60 (Grade A)** in about 4–5 days of work.

**The one-sentence rationale:** *B has the body, A has the brains — and the body is far harder
to build than the brains are to move.*

---

## 📊 Score summary

| Category | Max | Project A | Project B |
|---|:--:|:--:|:--:|
| Design | 15 | 8 | **15** |
| Development | 10 | 6 | **9** |
| Monitoring | 5 | 2 | **3** |
| AI Integration | 10 | **7** | **7** |
| Agentic Behavior | 10 | 5 | **6** |
| Additional Architecture Features | 5 | 3 | **4** |
| Presentation & Documentation | 5 | 3.5 | **4.5** |
| **TOTAL** | **60** | **34.5** | **48.5** |
| **Grade** | | **D/F** | **B** |

*Full per-criterion table with deciding evidence: `00-executive-summary-and-scoring.md`.*

---

## 📂 Read in this order

| # | Document | What it gives you |
|---|---|---|
| 1 | **[`00-executive-summary-and-scoring.md`](00-executive-summary-and-scoring.md)** | The verdict, the full 12-criterion scoring table, measured code metrics, and the complete pros/cons of both projects |
| 2 | **[`01-detailed-comparison.md`](01-detailed-comparison.md)** | Dimension-by-dimension deep dive with file-level evidence, plus a 12-item risk register for the defense |
| 3 | **[`02-modification-plan.md`](02-modification-plan.md)** | The prioritised backlog: 12 changes in 3 waves, each with criterion, point gain, effort and exact files. Includes the "harvest from A" and "do NOT harvest from A" lists |
| 4 | **[`03-oral-defense-plan.md`](03-oral-defense-plan.md)** | Minute-by-minute 60-minute agenda, demo choreography, and 15 prepared answers to the hardest questions |
| — | [`evidence\`](evidence/) | The six raw specialist agent reports (204 KB) backing every claim |

---

## 🔬 Method

Six specialist agents analysed both repositories in parallel, each owning specific rating-grid
criteria: architecture & design patterns, security & compliance, delivery & completeness,
observability, AI & agentic behaviour, and presentation & documentation. Every agent was
instructed to verify claims against source code rather than READMEs, and to grade skeptically.

Independent code metrics were measured separately (excluding `node_modules`, `.venv`, `bin`,
`obj`, build bundles), and the four verdict-critical findings were **re-verified by hand**:

| Finding | Verified at |
|---|---|
| ✅ B's CO₂ number is a calibration constant | `services\optimizer-worker\...\service.py:143` — `min(15.0, savings_pct * 0.84)` |
| ✅ B's peak reduction is clamped to `[3 %, 7 %]` | `services\optimizer-worker\...\service.py:132` |
| ✅ B's RUL has no physics | `services\scoring-worker\...\service.py:33-37` — `(thickness - 300.0) / degradation_rate` |
| ✅ B never calls a live LLM | `services\knowledge-orchestrator\...\adapters\azure_foundry.py:66` — `raise NotImplementedError` |
| ✅ A has a genuine MILP | `workloads\p2_energy_dispatch\milp.py:54-96` — `LpProblem`, binary vars, no-overlap constraints, CBC solver |
| ✅ A's Fabric pause/resume is unauthenticated | `apps\...\Program.cs:71,83` — `MapPost` with **zero** `RequireAuthorization` / `UseAuthentication` anywhere in the file |

---

## ⚡ The three things to do first

1. **M1** — Replace B's `savings_pct * 0.84` CO₂ constant with A's real PuLP MILP.
2. **M2** — Replace B's `(thickness - 300) / rate` with A's heat-flux regression, and delete
   the `demo_warning` hard-code in the Fabric notebook.
3. **M3** — Implement `extract_draft` so a real model is actually called, using A's prompts and
   citation enforcement inside B's hardened Foundry landing zone.

These three alone cross the **Grade A** boundary and remove every finding that could
*lose* the defense rather than merely cost points.

---

## ⚠️ The two things that could sink you

| | Risk | Fix |
|---|---|---|
| 🔴 | A juror greps B's optimizer and finds the headline CO₂ number is `× 0.84`, or greps the RUL and finds no physics behind a slide that says "physics-informed" | **M1 + M2** |
| 🔴 | *"Which model are you calling?"* — B's honest answer today is *"none"* | **M3** |

Both are fixed by copying code that already exists and works in Project A.
