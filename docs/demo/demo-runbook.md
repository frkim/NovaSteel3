# NovaSteel 15-Minute Demo Runbook

## 1. Demo objective

In 15 minutes, show how NovaSteel connects live plant signals to a Fabric data core, predicts furnace-lining risk 21 days ahead, optimizes energy against spot prices, improves quality, and captures retiring-operator knowledge. Every screen and spoken claim must identify the data as synthetic and distinguish predictions from measured outcomes.

## 2. Audience personas and tabs

Keep these browser tabs open and ordered:

1. **Plant Manager / Executive** — fleet KPIs, output, energy, CO₂, quality yield, ROI, and audit roll-up.
2. **Reliability Engineer** — furnace thermal map, lining RUL, alert and work order.
3. **Energy Manager** — spot price, baseline/optimized dispatch, constraints and savings.
4. **Quality Engineer** — genealogy, process drift, predicted/measured quality.
5. **Operator Knowledge** — interview, STT transcript, extracted procedure draft.
6. **Fabric Core** — Eventstream, lakehouse/warehouse lineage, freshness, quarantine.
7. **Demo Control** — scenario, accelerated clock, health, reset and fallback controls.

Use a separate browser profile with notifications disabled, zoom at 90-100%, no personal bookmarks, and no production tenant tabs.

## 3. Preflight

### 3.1 One business day before

- Confirm the tenant/workspace contains synthetic data only.
- Run the deterministic scenarios with seeds `240726`, `240727`, and `240728`.
- Verify the data-contract report is green and expected KPI ranges match the scenario manifest.
- Confirm the 45-day history is loaded, semantic model refreshed, and persona pages render.
- Confirm the 21-day alert is initially hidden and appears only at its cue.
- Verify the optimization has a feasible cached result and zero hard-constraint violations.
- Test microphone permission, synthetic fallback audio, STT, and transcript extraction.
- Export offline fallbacks: dashboard screenshots/PDF, a 90-second screen recording, alert JSON, optimizer result JSON, transcript text, and procedure draft.
- Cache all needed pages in the demo browser and record direct URLs in presenter notes.
- Rehearse once in online mode and once with network disabled.

### 3.2 Thirty minutes before

- Connect power and wired network; disable sleep, OS notifications, chat pop-ups, and automatic updates.
- Set display resolution and duplicate/extend mode; keep speaker notes on the private screen.
- Open the seven tabs in order and authenticate.
- Reset the demo to `READY`, seed `240725`, accelerated clock paused.
- Confirm every tab shows **Synthetic demo data — not for operational control**.
- Confirm data freshness is green, event counts are increasing when briefly unpaused, then pause again.
- Verify local fallback files open without network access.
- Close terminals containing unrelated paths, tokens, or history.

If a Python-based simulator must be installed or restored, direct it only to the approved Microsoft-protected feed:

```powershell
$env:PIP_CONFIG_FILE = "$PWD\pip.conf"
$env:PIP_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
$env:PIP_EXTRA_INDEX_URL = ""
& .\services\bff-api\.venv\Scripts\python.exe -m pip install `
    --disable-pip-version-check `
    -r .\services\bff-api\requirements.txt
```

The committed requirements are exact-version pins; they do not currently carry
hash entries, so do not add `--require-hashes` to this command. Never use public
PyPI, `--extra-index-url` to public registries, or an unapproved package source.
Ideally, install nothing on demo day.

### 3.3 Five minutes before

- Set scenario `demo-full`, root seed `240725`, speed `60x`.
- Confirm control status: `history=loaded`, `stream=paused`, `alert=armed`, `fallbacks=ready`.
- Put Plant Manager tab on screen.
- Start a visible 15-minute presenter timer.
- Have the reset operator and presenter agree on the hand signal for switching to fallback.

## 4. Minute-by-minute script

This order is binding with the six demo moments in [solution requirements](../specs/solution-requirements.md) and [personas and journeys](../personas/personas-and-journeys.md): DM-1 (0:00–2:00), DM-2 (2:00–4:30), DM-3 (4:30–7:00), DM-4 (7:00–9:30), DM-5 (9:30–12:00), DM-6 (12:00–14:00), then a one-minute recap/buffer.

| Time | Persona/tab and action | Presenter narrative | Proof point / fallback |
|---|---|---|---|
| 00:00-01:00 | **Plant Manager**. Show four-country fleet and select Moselle Integrated Works. | “NovaSteel unifies production, energy, emissions, quality, maintenance, and operator knowledge. Everything shown is deterministic synthetic data.” Point out energy at 35% of modeled production cost and the four target outcomes. | If dashboard is slow, use cached fleet overview. Do not wait more than 10 seconds. |
| 01:00-02:00 | **Fabric Core**. Show live Eventstream input, bronze-to-silver-to-gold lineage, freshness, and contract status. | “Captors publish event-time data through the edge; Fabric retains the immutable envelope, deduplicates and normalizes units, and serves one governed semantic layer.” Point to synthetic labels, schema version, and quarantine count. | Use a pre-recorded 20-second Fabric clip or architecture screenshot; continue speaking while switching. |
| 02:00-03:00 | **Demo Control**, then **Energy Manager**. Unpause at 60x and show day-ahead price with the baseline dispatch. | “We are accelerating time, not fabricating UI updates. Sequence, event time, lineage, and seed remain reproducible. The urgent automotive coil is fixed; only eligible reheat batches have flexibility.” | If stream is unavailable, start local replay; otherwise use the cached `evening-scarcity` price curve. |
| 03:00-04:30 | **Energy Manager**. Run or reveal the optimized schedule and constraint report. | Compare baseline and optimized Gantt charts. “The optimizer preserves soak times, delivery commitments, equipment capacity, and planned tonnage. This is a simulated/shadow approval, not a production schedule write.” Show 8-13% modeled cost reduction and 3-7% lower peak. | Reveal cached feasible solution after 5 seconds; show the saved result and constraint table. |
| 04:30-05:30 | **Reliability Engineer**. Open `LUX-BF-01`, hearth sector 07 thermal map. | “A localized warm zone is developing. Neighboring thermocouples, cooling-water ΔT, and heat-flux residual agree, so this is unlike a single bad sensor.” | Static thermal-map sequence has healthy, emerging, and degraded frames. |
| 05:30-06:30 | Continue the reliability trend and trigger the threshold. | Show 45-day thermal history compressed into seconds. Point to rising 6-hour slope and slower post-tap cooling; avoid claiming certainty. | Use cached animated chart; manually advance three frames if animation stalls. |
| 06:30-07:00 | Open the alert drawer, acknowledge it, and create/link the synthetic work-order record. | “The model estimates P50 remaining life at **21 days** with P10/P90 uncertainty. The engineer remains accountable: the platform recommends verification and records a synthetic work order; it does not actuate the furnace.” | Open saved alert JSON and pre-created `WO-DEMO-LUX-1042`; ensure P10 < 21 < P90 and risk ≥0.80. |
| 07:00-08:00 | **Quality Engineer**. Open `NS-AUTO-DP780` genealogy and drift panel. | “Coiling temperature and force balance are drifting together. The model warns before the first off-spec lab result and traces the affected heat, slab, coil, and process settings.” | Cached coil `COIL-LUX-260725-017` has complete genealogy. |
| 08:00-09:30 | Run the bounded quality what-if. | “A bounded what-if returns predicted first-pass yield from about 88% to 95%—roughly the target 8% relative improvement—without changing the grade recipe.” Toggle predicted versus measured labels; no setpoint is written. | Use cached what-if result; do not imply an automatic control write-back. |
| 09:30-10:30 | **Operator Knowledge**. Start interview or play fallback synthetic audio. Ask: “What do you check when hearth sector temperature rises but cooling flow appears normal?” | Show STT confidence and speaker labels. State that the operator has consented in this synthetic workflow and that the voice/persona is fictional. | If microphone/STT fails, play the approved WAV; if audio fails, paste the approved transcript and say it is replay mode. |
| 10:30-11:30 | Show extracted knowledge. | Highlight trigger, observations, checks, rationale, cautions, and source citations. Convert it to a draft procedure: verify neighboring sensors, compare water ΔT, inspect flow restriction, escalate for ultrasound. | Load pre-extracted fact JSON. Keep status `DRAFT — EXPERT REVIEW REQUIRED`. |
| 11:30-12:00 | Show the reviewer boundary. | “The Foundry draft cannot publish. A Knowledge Engineer reviews, edits, and approves a version before it enters retrieval.” | Use the saved approval-queue view; do not simulate an unreviewed procedure as published. |
| 12:00-13:00 | **Plant Manager / Sustainability view**. Show CO₂ trajectory, ETS exposure, and the energy-decision lineage. | “The carbon target and any financial claim remain targets. Here the semantic model rolls up synthetic emissions and connects a recommendation to its evidence.” | Use the cached sustainability/ETS report or the optional internal Power BI report tab. |
| 13:00-14:00 | **Executive / audit view**. Show portfolio targets, ROI roll-up, and one append-only decision record. | “Every recommendation links inputs, model/version, confidence, human decision, and outcome. The 14/22/21/8 figures are targets; the screen is synthetic evidence of traceability.” | Use exported audit JSON/PDF and cached board-report view. |
| 14:00-15:00 | **Plant Manager**, then briefly **Fabric Core**. | Recap: “One Fabric core connects streaming operations, governed history, models, decisions, and human knowledge.” End on lineage/freshness and the next-step invitation. | If any tab is unstable, finish on cached summary slide. Stop at 15:00 rather than debugging live. |

## 5. Expected cue sheet

| Cue | Expected value/state |
|---|---|
| Stream start | `ONLINE`, freshness <5 s, event rate visibly nonzero |
| Lining target | `LUX-BF-01 / HEARTH-SECTOR-07` |
| RUL alert | P50 21.0 days; P10 16.8; P90 27.5; risk 0.87; `HIGH` |
| Work order | `WO-DEMO-LUX-1042`, synthetic, planned inspection |
| Price peak | 280 EUR/MWh evening scarcity interval |
| Energy outcome | 8-13% modeled cost reduction; equal tonnage; zero hard violations |
| Quality coil | `COIL-LUX-260725-017`, `NS-AUTO-DP780` |
| Quality outcome | Predicted first-pass yield approximately 88% -> 95% |
| Knowledge status | Draft, cited to transcript, expert review required |
| Fabric health | Bronze/silver/gold current; quarantine only intentional negative tests |

If a value lands outside its expected band, switch to the cached deterministic result rather than changing the narrative or hiding the discrepancy.

## 6. Offline and degraded-mode strategy

### 6.1 Fallback ladder

Use the first working level and clearly say “replay” or “cached result”:

1. **Live cloud** — Fabric stream, semantic model, model endpoints, live STT.
2. **Local deterministic replay** — pre-generated event file and local UI/API, no external calls.
3. **Cached interactive** — static historical model plus saved inference/optimization/transcript responses.
4. **Recorded flow** — short chapter videos with presenter narration.
5. **Static proof pack** — screenshots/PDF and JSON examples.

Do not spend more than 10 seconds diagnosing during the 15-minute presentation. The audience should see an intentional fallback, not a terminal error.

### 6.2 Required fallback pack

Store the pack in an access-controlled, offline-capable demo folder and verify checksums:

- fleet overview and persona screenshots;
- 45-day thermal trend and three-frame hearth map;
- `model-inference` and alert-lifecycle JSON;
- baseline and optimized schedule/results;
- quality genealogy, drift, and what-if results;
- licensed synthetic interview WAV, transcript, extracted facts, and procedure draft;
- Fabric architecture/lineage image and contract-health report;
- 90-second end-to-end recording;
- scenario manifest, expected values, and reset checklist.

The fallback pack must contain no credentials, production endpoints, real customer identifiers, real operator voices, or personal data.

## 7. Operator interview script

Use a fictional identifier, for example `OP-DEMO-014`, role “Senior Blast Furnace Operator (synthetic).”

Presenter questions:

1. “What do you check when one hearth sector warms but cooling flow appears normal?”
2. “How do you tell a failing thermocouple from real lining degradation?”
3. “What should a new operator never change without engineering approval?”

Approved synthetic answer content:

- compare the sector with neighboring shell thermocouples;
- check cooling-water inlet/outlet temperature and recent flow history, not only the current flow;
- look for persistence across taps and slower cooling after a tap;
- validate sensor health and recent calibration;
- request cooling-circuit inspection and ultrasound measurement when signals agree;
- do not bypass alarms or change furnace/cooling controls from the interview guidance.

The extraction must retain source segment citations and separate `observation`, `recommended_check`, `rationale`, and `safety_boundary`. The procedure remains a draft until reviewed by reliability, operations, and safety owners.

## 8. Failure handling during the demo

| Symptom | Immediate action | Spoken bridge |
|---|---|---|
| No live events | Switch to local replay, then recorded stream | “I’ll switch to our deterministic replay so we can keep the same event sequence.” |
| Fabric tab inaccessible | Show lineage screenshot/clip | “This is the cached lineage view from the same validated run.” |
| Model endpoint slow | Reveal saved inference | “For a predictable demo we cache the signed result from this exact seed.” |
| Optimizer infeasible | Load known feasible result; show constraints | “The platform never relaxes hard production constraints silently.” |
| STT fails | Play WAV, then paste approved transcript | “We support offline replay; the review workflow is unchanged.” |
| Browser crashes | Reopen direct URL or static summary | “The data and decisions are persisted; the presentation client is replaceable.” |
| Incorrect cue/value | Stop stream and load expected manifest result | “The live run differs from the rehearsed seed, so I’m switching to the validated scenario.” |
| Network fully lost | Use fallback ladder levels 2-5 | “The edge buffers data and preserves event time; here is the offline path.” |

Never expose stack traces, tokens, tenant details, or hidden production-like settings on the projector.

## 9. Recovery and reset

### 9.1 Soft reset between rehearsals

1. Pause the accelerated clock.
2. Stop publishers cleanly and wait for in-flight batches to drain.
3. Set scenario to `demo-full`, root seed `240725`, simulated start time to the manifest value.
4. Clear only the synthetic run's hot cache, alert state, demo work-order link, interview session, and UI selections.
5. Preserve the preloaded historical partitions and cached fallback artifacts.
6. Restore model responses and optimizer outputs from the matching manifest.
7. Reset alert to `ARMED`, stream to `PAUSED`, persona to Plant Manager.
8. Start for 30 seconds; verify sequence, event count, expected checksum, freshness, and synthetic labels.
9. Pause and mark control state `READY`.

### 9.2 Hard recovery

Use when the run is contaminated, sequence state is unknown, or scenario outputs do not reconcile:

1. Stop the simulator and disconnect its publisher.
2. Record the failed `run_id`; do not delete evidence until after diagnosis.
3. Create a new `run_id` and isolated synthetic namespace.
4. Reload the signed reference snapshot and historical scenario data.
5. Reset sink checkpoints/deduplication state for the new namespace only.
6. Replay the manifest and run contract, physical, and scenario assertions.
7. Refresh the semantic model and verify the cue sheet.
8. Reopen the seven tabs, test fallback files, and return to `READY`.

Never truncate a shared or production table, clear a shared event stream, or reuse production secrets as part of reset.

### 9.3 Post-demo

- Pause and stop the simulator.
- Save the run manifest, timestamps, and demo health report.
- Delete ad hoc microphone recordings unless retention was explicitly approved; retain only the approved synthetic artifact.
- Close sessions, remove temporary access grants, and confirm no publisher remains active.
- Record any fallback used and rehearse the failed chapter before the next presentation.

## 10. Go/no-go checklist

Proceed only when:

- all displayed data is labeled synthetic;
- deterministic manifests and expected cues validate;
- live stream and at least two fallback levels work;
- alert, optimizer, quality, and knowledge cached results are available;
- microphone/audio and privacy messaging are tested;
- no production credentials or data are visible;
- reset completes in under five minutes;
- presenter can finish the story entirely offline.

If any synthetic-data boundary, privacy control, or safety disclaimer is missing, the demo is **no-go**.
