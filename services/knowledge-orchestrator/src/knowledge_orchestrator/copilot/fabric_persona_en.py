"""English answers served for the Copilot's per-persona predefined questions.

Every figure below is synthetic demo data: it is the value already shown on the
matching screen, emitted by the device simulator, or recorded in the verified
July-2026 gold scorecard. Keep prose and numbers in sync with the fixture pack --
the whole point of these answers is that an operator can check them against the
screens.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- plant-manager -------------------------------------------------------
    "persona-plant-manager-q1": """**There is no single line-level day KPI in this demo pack.** The closest live proxy is **LUX-RHF-01**, the reheat line that falls furthest away from plan during the scarcity window.

- Site throughput is **128.4 t/h** against a **130 t/h** target, with OEE **84.1%** against 85%
- Between **17:00 and 20:00** the reheat profile drops to about **114-122 t/h**
- That window coincides with the **€280/MWh** evening spike, so the dip is deliberate load shifting rather than an unplanned stoppage
- Downstream quality still needs watching because **COIL-LUX-260725-017** is carrying a **+11.4 °C** coiling bias

If you want the one line furthest behind in operational terms, triage the reheat furnace window first. The consequence is commercial rather than catastrophic: you are trading a short throughput dip for cheaper energy and lower Scope 2 exposure.""",
    "persona-plant-manager-q2": """**The pack does not hold a crew-labelled yield ledger for the night shift.** The closest evidence points to a local quality drift, not to a plant-wide metallurgical swing.

- The current fail batch is **COIL-LUX-260725-017** on **LUX-HSM-01**, with a **+11.4 °C** coiling bias
- Yield strength is **452.4 MPa** against a **380-520 MPa** spec, so the steel is still inside band, but the lab result is **REVIEW**
- SPC puts subgroup **20** at **11.4**, above the **8.5** upper control limit
- Across July 2026 there are **86 defects**, and coiling-temperature drift accounts for **34 (39.5%)**, ahead of edge crack 21 and surface scale 14

Start the morning with hot-strip coiling control, release discipline on the DP780 coil, and confirmation that the drift was assignable rather than systemic. That is the highest-probability cause you can act on first.""",
    "persona-plant-manager-q3": """**Start with the hearth, then the dispatch, then the DP780 quality drift.** That is the cleanest triage order this morning.

- **1. Furnace** - **ALERT-HEARTH-SECTOR-07-260725** is the only critical alert: risk **0.8995**, **P50 19.65 days**, lining **363 mm** against a **300 mm** minimum
- **2. Energy** - **REC-DEMO-LUX-240725** is still waiting for approval and is worth **€2,688.70** or **7.25%**, with peak demand down from **56.0 MW** to **51.58 MW**
- **3. Quality** - **COIL-LUX-260725-017** is carrying **+11.4 °C** coiling bias and the subgroup-20 SPC breach
- Board state is **16 open alerts**: **1 critical, 8 warning, 7 info, 2 acknowledged**

That order protects safety and availability first, captures today’s largest controllable cost and carbon lever second, and then deals with the most visible customer-facing quality risk.""",
    "persona-plant-manager-q4": """**84.1%** right now, against an **85%** target.

- Throughput is **128.4 t/h** versus **130 t/h**
- On-time delivery is **96.4%** versus 97%
- Energy intensity is **€312/t** versus **€300/t**
- The visible performance drag is concentrated in the **17:00-20:00** scarcity window, where reheat output runs at roughly **114-122 t/h**

So the plant is close to the OEE target, but not on it. The important reading is that the shortfall is being bought in a controlled way to avoid **€280/MWh** electricity, not because the line has fallen into unstable running. The operational consequence is to keep the energy trade-off explicit rather than treating it as hidden throughput loss.""",
    # -- furnace-operator ----------------------------------------------------
    "persona-furnace-operator-q1": """**The BF-01 hearth profile is asymmetric, not uniformly hot.** The watch item is **SECTOR-07**.

- **SECTOR-07** is rising at **3.4 °C/h** from about **652 °C**
- The other sectors are only moving around **0.4 °C/h**, so the issue is divergence, not a whole-hearth shift
- Local heat flux is **118 kW/m²**
- Cooling still looks nominal at **198 m³/h** with a water **ΔT of 9.4 °C**
- The refractory estimate falls from **372 mm** to **363 mm** over 24 hours

That combination is why the model weights **heat_flux_6h_slope** at **29%**, **sector_to_ring_temp_delta** at **24%**, and **cooling_efficiency_residual** at **18%**. The consequence is that you should treat this as a real localised wear signal, not as a harmless whole-furnace warm-up.""",
    "persona-furnace-operator-q2": """**The demo does not carry a sensor tagged T12-North.** The closest live evidence is **TC-114** drifting and the shell on **SECTOR-07** running away from its neighbours.

- **TC-114** is drifting at **1.8 °C/h**
- **SECTOR-07** is climbing at **3.4 °C/h** from **652 °C**, while neighbouring sectors sit near **0.4 °C/h**
- Heat flux is already **118 kW/m²**
- Cooling water is still at **198 m³/h** with **ΔT 9.4 °C**, so a simple water-loss explanation does not fit the pattern

So the best-supported explanation is not 'one bad north sensor' but a genuine local thermal change that is also visible in the physics-informed score. The operational consequence is to verify TC-114 against adjacent thermocouples, but to keep acting as if the hearth signal is real until that check clears it.""",
    "persona-furnace-operator-q3": """**There is no live tap-parameter table in this platform.** The closest governed evidence is **PROC-DEMO-0002**, plus the fact that today’s abnormality is in hearth thermal behaviour rather than in a tapped-heat chemistry window.

- **PROC-DEMO-0002** is the approved procedure: status **APPROVED**, version **3**
- **PROC-DEMO-0001** is still **IN_REVIEW**, so it can inform checks but should not be treated as operating authority
- Current context is thermal: heat flux **118 kW/m²**, cooling **198 m³/h**, **ΔT 9.4 °C**, and sector 07 rising at **3.4 °C/h**
- The process chain still runs blast furnace to steelmaking to caster; nothing in the evidence says to freehand the next cast

So do not invent a tap adjustment from this screen. The consequence is procedural: run the approved inspection and confirmation steps first, then change cast practice only if a governed BOF or caster instruction explicitly tells you to.""",
    "persona-furnace-operator-q4": """**The platform does not quantify a standalone coke-rate-to-wear curve.** What it does show is that today’s wear signal is being dominated by thermal stress.

- The top model driver is **heat_flux_6h_slope at 29%**
- Next is **sector_to_ring_temp_delta at 24%**
- Then **cooling_efficiency_residual at 18%**
- The live thermal state behind that is **118 kW/m²** heat flux, **198 m³/h** cooling flow and water **ΔT 9.4 °C**
- The estimate is already down to **363 mm** lining thickness versus a **300 mm** safe minimum

So the honest answer is that coke rate may matter as a covariate, but the current score is not being driven by a proven coke-rate elasticity. The operational consequence is to control what is directly evidenced now - heat load, sector imbalance and cooling effectiveness - rather than chasing an unsupported coke-only explanation.""",
    # -- maintenance-engineer ------------------------------------------------
    "persona-maintenance-engineer-q1": """**LUX-BF-01 / HEARTH-SECTOR-07** is the clear top risk this week.

- Risk score **0.8995** with **P50 19.65 days**, **P10 18.69**, **P90 20.61**
- Estimated thickness **363 mm** against a **300 mm** minimum
- Degradation is running at about **3.0 mm/day**
- The next named asset in the pack, **LUX-RHF-01**, is only around **34%** risk with roughly **120 days** left
- Work order **WO-DEMO-LUX-1042** already exists for a planned inspection

There is no close second inside the same urgency band. The consequence is to lock the inspection and reline planning window around BF-01 first; everything else is watch-list work, not this-week intervention.""",
    "persona-maintenance-engineer-q2": """**Because the live thermal picture is steeper than the historical alert episodes.** The model is seeing a faster local deterioration signal, not just replaying the old average path.

- The refractory estimate moves from **372 mm** to **363 mm** over 24 hours
- **SECTOR-07** is rising at **3.4 °C/h** while neighbouring sectors sit near **0.4 °C/h**
- The score is still anchored by the same driver stack: **29%** heat-flux slope, **24%** sector-to-ring delta, **18%** cooling-efficiency residual
- Cooling remains nominal at **198 m³/h** and **ΔT 9.4 °C**, which makes the sector divergence harder to dismiss as instrumentation noise

Historically, July alert episodes prove the system can hold a planned reline at **21.0 days** of warning. Today’s fall to **P50 19.65 days** means the current wear signature is already inside that comfort margin. The consequence is to compress planning and inspection cadence, not to wait for history to average it away.""",
    "persona-maintenance-engineer-q3": """**Schedule the BF-01 inspection sequence now, and keep the reline window inside days 18-24.** That is the governed plan supported by the current evidence.

- **WO-DEMO-LUX-1042** is the live maintenance object
- Inspection days **1-4**: confirm thermocouples, cooling inlet and outlet temperatures, and local history
- Ultrasound and thickness confirmation days **5-8**
- Planned reline window **days 18-24**
- Anchor figures are risk **0.8995**, **P50 19.65 days**, and **363 mm** lining versus **300 mm** minimum

Use **PROC-DEMO-0002** as the approved operating procedure; **PROC-DEMO-0001** is still in review and should stay advisory. The consequence is that you still have time to make this a planned stop, but only if the inspection sequence starts immediately.""",
    "persona-maintenance-engineer-q4": """**P50 is 19.65 days; P90 is 20.61 days.** They are not two different futures, but two different confidence points on the same predicted remaining-life distribution.

- **P10 18.69 days** - a conservative lower bound
- **P50 19.65 days** - the median estimate, the value most people use for day-to-day planning
- **P90 20.61 days** - an optimistic upper bound with more remaining life than the median
- The spread is tight: only **0.96 days** from P50 to P90

Against a programme target of **21 days** of advance warning, all three numbers tell the same story: you are effectively inside the action window already. The operational consequence is to plan with P50, stress-test with P10, and use P90 only to understand upside - not to justify waiting.""",
    # -- energy-manager ------------------------------------------------------
    "persona-energy-manager-q1": """**02:00-05:00** is the next low-carbon window carried in the demo, helped by the **12 MWh** wind PPA block.

- The expensive, dirtier window is **17:00-20:00**, with prices up to **€280/MWh**
- The dispatch recommendation moves flexible reheat away from that scarcity period
- One visible move is **REHEAT-BATCH-06** from slot **75** at **18:45** to slot **67** at **16:45**
- The day-level impact is **€37,109.10** baseline to **€34,420.40** optimised, saving **€2,688.70** or **7.25%**

So the next clean window is not just cheaper electricity; it is the part of the day where the schedule can take load without paying the carbon premium of the evening peak. The consequence is to pull flexible heating and melting forward or later, not let it sit inside the 17:00-20:00 band.""",
    "persona-energy-manager-q2": """**Because tonnes dipped while fixed load did not.** The last shift’s energy-intensity spike is best explained by the deliberate reheat load shift through the scarcity window.

- Energy intensity is **€312/t** against a **€300/t** target
- Throughput is **128.4 t/h** against **130 t/h**, but in the **17:00-20:00** window it falls to roughly **114-122 t/h**
- That is exactly where spot price peaks at **€280/MWh**
- The dispatch keeps total tonnage unchanged at **960 t**, so the schedule is buying cost and carbon relief with a short-rate dip

In other words, the spike is an arithmetic effect of lower instantaneous output against a largely fixed plant load, not evidence that the plant suddenly became intrinsically inefficient. The operational consequence is to judge €/t together with the dispatch objective, not in isolation.""",
    "persona-energy-manager-q3": """**REC-DEMO-LUX-240725** is the biggest visible save in the pack, and the key move is the reheat batch that leaves the 18:45 slot.

- Baseline **€37,109.10** to optimised **€34,420.40** - saving **€2,688.70** or **7.25%**
- Peak demand falls from **56.0 MW** to **51.58 MW**
- **REHEAT-BATCH-06** moves from slot **75** at **18:45** and **€280/MWh** to slot **67** at **16:45** and **€97.24/MWh**
- That single move cuts batch cost from **€3,920.00** to **€1,361.36**
- In July 2026, **100 of 116** recommendations were accepted, adoption **0.862** against a 0.70 target

So the highest-value opportunities are the flexible thermal loads that still touch the scarcity band. The consequence is to approve the dispatch quickly and keep looking for evening-window reheat or melt moves of the same pattern.""",
    "persona-energy-manager-q4": """**The platform does not carry an EAF-specific off-peak what-if on this card.** The closest measured evidence is the dispatch already modelled on flexible thermal load.

- That dispatch reduces CO₂ by **3.29%** at unchanged tonnage
- The full-plan optimisation case on the sustainability summary is **8.7%**
- Grid carbon averages about **244 gCO₂/kWh**, so moving load into cleaner hours cuts Scope 2 without changing steel output
- The same dispatch also cuts peak demand from **56.0 MW** to **51.58 MW**

So I would not quote a separate EAF-heats figure that the pack does not prove. What the platform does prove is the mechanism: off-peak movement trims purchased-electricity emissions directly. The operational consequence is to treat load-shifting as a real Scope 2 lever even when throughput and tonnage stay flat.""",
    # -- quality-engineer ----------------------------------------------------
    "persona-quality-engineer-q1": """**COIL-LUX-260725-017** is the only current **FAIL** on the live Luxembourg board, and it is the one to pull first.

- Grade **NS-AUTO-DP780**
- Risk score **0.429**
- Coiling-temperature bias **+11.4 °C**, the largest visible deviation
- Measured yield strength **452.4 MPa** against a **380-520 MPa** spec
- Lab status **REVIEW**, and the quality alert remains acknowledged but open

The platform does not expose a separate multi-coil 'surface only' fail list on this screen, so this is the closest truthful answer to a quality-check failure call. The operational consequence is to quarantine or review this coil before release and then trace the drift back through reheat and coiling rather than assuming a general lab problem.""",
    "persona-quality-engineer-q2": """**There is no asset called Line 3 in the demo model.** The closest real line evidence is **LUX-HSM-01**, and the drift is being led by coiling temperature rather than by a broad product mix change.

- July 2026 records **86 defects** in scope
- **34 defects (39.5%)** are coiling-temperature drift, ahead of edge crack **21**, surface scale **14**, thickness variance **9**, coating **5** and other **3**
- The current special-cause point is subgroup **20** at **11.4**, above the **8.5** UCL
- The affected coil is **COIL-LUX-260725-017** with **+11.4 °C** bias on **LUX-HSM-01**

So the trend is not best read as 'Line 3 is getting worse'; it is better read as one dominant failure mode on the hot-strip route. The operational consequence is to stabilise coiling control first, because that is where both the live breach and the monthly defect mix are pointing.""",
    "persona-quality-engineer-q3": """**The platform does not score centreline segregation as its own KPI.** The closest real evidence sits on the caster inputs and the genealogy behind the affected coil.

- The live caster variables available for this kind of triage are **superheat**, **casting_speed** and **secondary_cooling_flow** on **LUX-CC-01**
- The genealogy is complete: **LOT-FE-017 → H-LUX-260725-0040 → LADLE-017 → SLAB-017 → REHEAT-017 → COIL-LUX-260725-017 → SMP-017 → SHIP-DEMO-017**
- The coil’s measured yield strength is **452.4 MPa**, still inside the **380-520 MPa** band, with lab status **REVIEW**

So I would use the caster trio as the correlation set and keep the genealogy open through reheat and coiling. The operational consequence is to investigate segregation-like risk as a route problem spanning caster thermal practice and downstream reheating, not as a standalone lab number that appears from nowhere.""",
    "persona-quality-engineer-q4": """**The SPC on this screen is not for thickness directly; it is for coiling-temperature bias.** What it tells you is still operationally important.

- Mean **1.9**, sigma **2.2**, upper control limit **8.5**, lower control limit **-4.7**
- Subgroup **20** reads **11.4**, so it is out of control on the high side
- Process capability is **Cpk 1.18** against a **1.33** target
- The same **11.4** value matches the coiling bias on **COIL-LUX-260725-017**

So SPC is telling you there is a fresh special cause in thermal handling, not that the whole process centre has drifted gradually. The consequence is to investigate the assignable coiling-temperature cause first; only after that should you infer anything about thickness performance from the same production run.""",
    # -- sustainability-officer ---------------------------------------------
    "persona-sustainability-officer-q1": """**Mostly yes, but the quarter is no longer comfortable.** Allowance usage is already **71%**, and headroom is down to **6.2%**.

- Current allowance price is **€86/t**
- Exposure forecast is about **€248,000** at the present operating point
- Current fixture intensity is **1.42 tCO₂e/t** against a **1.35** target
- The live ledger alert for this is the open **ALERT-ETS-ALLOWANCE-Q3**
- Closed-book July 2026 still looks strong at **1.019 tCO₂e/t** against a **1.638** target and **2.10** baseline

So the programme is on track in the historical scorecard, but the current quarter cushion is thin. The operational consequence is to keep using load-shifting and other near-term levers now, because a few weak operating days would burn the remaining 6.2% headroom quickly.""",
    "persona-sustainability-officer-q2": """**The platform does not carry a CBAM-specific exposure column.** The closest proven proxy is ETS exposure plus current Scope 1 intensity.

- Today’s Scope 1 load is **1,368 t CO₂e/day** for **960 t** of steel, or about **1,425 kg/t**
- A straight **10%** production lift at unchanged intensity would add roughly **136.8 t CO₂e/day**
- Allowance usage is already **71%**, with exposure forecast at **€248,000** and headroom at **6.2%**
- Current operating intensity sits at **1.42 tCO₂e/t** against a **1.35** target

So I would not claim a CBAM invoice number the data pack does not hold. What the evidence does say is that a 10% tonnage increase would materially increase carbon-priced exposure unless intensity improves at the same time. The operational consequence is to pair any output uplift with efficiency or dispatch action, not let tonnes rise on an unchanged emissions profile.""",
    "persona-sustainability-officer-q3": """**1.42 tCO₂e/t** on the current operating fixture.

- That is the live day figure, not the closed-book monthly average
- It sits above the **1.35** target for the current operating mode
- For the last closed month, July 2026, the plant landed at **1.019 tCO₂e/t**
- That July result beat the **1.638** target and the **2.10** baseline by a wide margin
- Scope split for July is **355,336 t** Scope 1 and **147,868 t** Scope 2

So your current intensity is worse than the monthly gold close, even though the programme trend is still ahead of target. The operational consequence is to read the 1.42 value as a live correction signal - especially around thermal load and electricity timing - not as a reason to doubt the month-end ledger.""",
    "persona-sustainability-officer-q4": """**Against the benchmark, the programme is ahead on the month and behind on the live day.** Both things are true at once.

- Current fixture: **1.42 tCO₂e/t** against a **1.35** target, so about **0.07 tCO₂e/t** high
- Closed-book July 2026: **1.019 tCO₂e/t** against a **1.638** target and **2.10** baseline
- Current quarter context: allowance usage **71%**, headroom **6.2%**, forecast exposure **€248,000** at **€86/t**
- Dispatch remains the fastest lever, cutting CO₂ **3.29%** on the demonstrated schedule

So compared with the benchmark, the system is winning in the historical ledger but under pressure in the present operating window. The operational consequence is to keep presenting both numbers together: the monthly score proves the programme works, while the live figure tells you today still needs active intervention.""",
    # -- knowledge-engineer --------------------------------------------------
    "persona-knowledge-engineer-q1": """**The fixture pack does not store per-term glossary lookup frequency.** The closest real evidence is demand and coverage by knowledge domain.

- Blast furnace coverage **82%**
- Quality lab **77%**
- Hot strip mill **71%**
- Reheat furnace **64%**
- Energy and utilities **58%**
- Procedure states are split across **PROC-DEMO-0001 IN_REVIEW v2**, **PROC-DEMO-0002 APPROVED v3** and **PROC-DEMO-0003 DRAFT v1**

So I cannot truthfully name the most-looked-up glossary term from this pack. What I can say is that the lowest-coverage domains are the likeliest lookup pressure points, especially energy and reheat. The operational consequence is to improve capture and approval there first, because that is where unsupported questions are most likely to accumulate.""",
    "persona-knowledge-engineer-q2": """**It cites the sources that are both relevant and governable, not just whatever text was retrieved.** In this platform the evidence chain is deliberately auditable.

- The decision ledger shows **AUD-0001** to **AUD-0005**, and all five have **complete_audit_flag true**
- Procedures are not equal: **PROC-DEMO-0002** is **APPROVED v3**, while **PROC-DEMO-0001** is **IN_REVIEW v2** and **PROC-DEMO-0003** is **DRAFT v1**
- For predefined persona questions, the Copilot uses fixed Fabric cards, so the cited datasets are deterministic rather than improvised

So the system prefers approved knowledge and complete audit chains over merely available text. The operational consequence is that a helpful-looking unapproved source should still stay out of the final answer if it cannot meet the same governance standard as the approved or audited evidence.""",
    "persona-knowledge-engineer-q3": """**The grounding architecture is layered and deliberately narrow.** The closest real evidence is the combination of governed procedures, Fabric facts and the ontology path that links assets through the process route.

- Governed text layer: **PROC-DEMO-0002 APPROVED v3**, with **PROC-DEMO-0001 IN_REVIEW v2** and **PROC-DEMO-0003 DRAFT v1** still outside the same trust level
- Analytical layer: Fabric gold facts for KPI history and KQL hot views for live state
- Structural layer: the ontology can trace paths such as **LUX-BF-01** forward through the steelmaking chain to **LUX-HSM-01**
- Decision layer: **AUD-0001..AUD-0005**, all with **complete_audit_flag true**

So the platform grounds answers on a small number of explicit retrieval routes rather than free synthesis. The operational consequence is predictability: you can inspect which data tier, procedure status or graph path supported the answer, instead of trusting a black-box summary.""",
    "persona-knowledge-engineer-q4": """**The platform does not expose a dedicated 'prompt-injection score' table in Fabric.** The closest operational evidence is that it already enforces approved-only grounding, complete audit records and human review before action.

- All five audit rows **AUD-0001** to **AUD-0005** are complete
- Only **PROC-DEMO-0002** is approved for direct operational use; **PROC-DEMO-0001** and **PROC-DEMO-0003** stay below that bar
- Recommendations such as **REC-DEMO-LUX-240725** remain pending human approval rather than auto-committing

So the real guardrails you can prove from the data are governance boundaries, traceability and human-in-the-loop control. The operational consequence is important: even if untrusted text were retrieved, it still lacks a direct path to approve a schedule, alter a control action or erase the audit trail.""",
    # -- ot-systems-engineer -------------------------------------------------
    "persona-ot-systems-engineer-q1": """**None are materially delayed or missing right now.** The live estate is healthy by the measures the platform actually carries.

- **17 devices** and **91 signals** are online
- Signal freshness is under **5 s** for the fast live feeds
- End-to-end freshness is about **12 s**
- Active incidents are **0**
- The quarantine alert threshold is **2% per 15 minutes**, and there is no evidence here of that threshold being breached

The one thing to remember is that not every signal is supposed to update at the same cadence: **hearth_refractory_estimate** is a **900,000 ms** signal by design, not a delayed 5-second feed. The operational consequence is that you do not need feed triage right now; you need to preserve the healthy path while you work the process alerts separately.""",
    "persona-ot-systems-engineer-q2": """**5,000 ms** for the fast hearth signals, with an overall platform freshness of about **12 s** end to end.

- **hearth_shell_temperature** publishes every **5,000 ms**
- **local_heat_flux** publishes every **5,000 ms**
- **hearth_refractory_estimate** is deliberately slower at **900,000 ms**
- The estate is still healthy overall: **17 devices**, **91 signals**, **0 incidents**
- **TC-114** drifting at **1.8 °C/h** is a thermal signal issue, not a network-latency proof point

So the furnace sensor network is not the bottleneck. The operational consequence is to separate data-path latency from process behaviour: the 5-second feeds are arriving on time, so the abnormal hearth trend should be treated as a plant condition rather than as a transport artefact.""",
    "persona-ot-systems-engineer-q3": """**The platform does not provide an in-product PLC-tag provisioning wizard.** The closest authoritative object is the telemetry event contract the gateway must publish.

- The envelope carries **source_id**, **asset_id**, **plant_id**, **sequence**, **schema_name** and **schema_version**
- The telemetry schema name is **novasteel.telemetry.v1**
- A good source id looks like **LUX-BF-01-TC-H07-03**, so the asset and signal identity stay explicit through the gateway
- Fast tags should align with the right cadence, such as **5,000 ms** for hearth shell temperature, while slower estimates can run at **900,000 ms**
- Badly shaped payloads are meant to land in quarantine rather than slip into silver unnoticed

So configuring a new PLC tag here means mapping it cleanly into the published envelope and signal registry, not editing a hidden analytics table. The operational consequence is that contract conformance matters as much as the tag itself, because the wrong shape will be rejected on purpose.""",
    "persona-ot-systems-engineer-q4": """**The wire protocol is not stored in Fabric.** What the platform proves is the gateway-mediated pattern above it.

- The live estate shows **17 devices** and **91 signals** with **0 incidents**
- Events arrive as versioned envelopes with source ids such as **LUX-BF-01-TC-H07-03**
- Health is measured through gateway connection state, freshness and queue behaviour, not through a protocol column
- End-to-end freshness is about **12 s**, and the fast thermal signals still publish every **5,000 ms**

So I would not pretend the analytics layer can tell you whether the thermal array is Modbus, Profinet or something else. The closest truthful answer is that the protocol is abstracted behind the plant gateway pattern, and the evidence you have here is that the bridge is healthy enough to deliver furnace telemetry on time. The operational consequence is to look in the OT registry for protocol specifics, not in the Fabric facts.""",
}
