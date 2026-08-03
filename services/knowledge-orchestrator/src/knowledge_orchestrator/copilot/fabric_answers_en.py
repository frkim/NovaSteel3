"""English answers served for the Copilot's predefined questions.

Every figure below is synthetic demo data: it is the value already shown on the
matching screen, emitted by the device simulator, or recorded in the verified
July-2026 gold scorecard. Keep prose and numbers in sync with the fixture pack --
the whole point of these answers is that an operator can check them against the
screen behind the panel.

Formatting note: the Copilot panel renders paragraphs, ``**bold**`` and
``_italic_`` only. Do not use tables, headings or code spans.
"""

from __future__ import annotations

from typing import Final

ANSWERS: Final[dict[str, str]] = {
    # -- command-center ----------------------------------------------------
    "command-center-q1": """**ALERT-HEARTH-SECTOR-07-260725** is the one to take first: it is the only CRITICAL alert open, and the only one with a reline behind it.

- Asset **LUX-BF-01**, component **HEARTH-SECTOR-07**, site NS-DEMO-LUX-01
- Remaining useful life **P50 19.65 days**, risk score **0.90**, model confidence 0.78
- Raised at **17:58**, still OPEN

Sixteen alerts are open across the four sites: **1 critical, 8 warning, 7 info, 2 acknowledged**. Everything else is a warning or lower - the evening price spike to €280/MWh, the DP780 coiling drift on COIL-LUX-260725-017, and Q3 ETS headroom at 6.2%.

Work order **WO-DEMO-LUX-1042** is already drafted against the hearth, so the decision waiting on you is the inspection window, not the diagnosis.""",
    "command-center-q2": """Four next-best actions are queued, one per domain.

- **Furnace** - schedule the BF-01 hearth inspection. Risk 0.90, RUL P50 19.65 days, work order WO-DEMO-LUX-1042 raised at 18:00.
- **Energy** - approve the 17:00-20:00 load shift. The tile shows a modelled savings band of about €4.2k; the committed dispatch REC-DEMO-LUX-240725 lands at **€2,688.70 (7.25%)** with peak demand down from 56.0 to 51.58 MW.
- **Quality** - review the NS-AUTO-DP780 drift on COIL-LUX-260725-017: coiling bias **+11.4 °C**, risk 0.429, status FAIL.
- **ETS** - Q3 allowance headroom is down to **6.2%**, with 71% of allowances used at €86/t.

Highest impact you can approve today is the dispatch. Highest impact you can avoid is the hearth failure, which the use case values at €8M per unplanned event.""",
    "command-center-q3": """Crew A (06:00-14:00, A. Weber) hands over to Crew B at **13:45**. Since the previous handover:

- **Escalated** - the hearth alert went CRITICAL at 17:58, risk 0.90, RUL P50 19.65 days
- **New** - evening scarcity warning at 15:12 (€280/MWh, 18:30-19:00) and the Q3 ETS headroom warning at 08:45
- **Acknowledged but still open** - DP780 coiling drift (04:00) and thermocouple TC-114 drift (21:10)
- **Raised** - work order WO-DEMO-LUX-1042 at 18:00; dispatch REC-DEMO-LUX-240725 remains PENDING_APPROVAL
- **Decisions recorded** - 5 audit entries, AUD-0001 to AUD-0005, across furnace, energy, quality, knowledge and capacity

Nothing was closed during the shift, so the open count is unchanged at **16 alerts**.""",
    "command-center-q4": """**REC-DEMO-LUX-240725**, the energy dispatch, is the recommendation with the highest approvable impact.

- Cost €37,109.10 baseline to **€34,420.40** optimized - a saving of **€2,688.70 (7.25%)** on the day
- Peak demand 56.0 MW to **51.58 MW**, down 7.89%
- CO₂ down **3.29%** at unchanged tonnage (960 t)
- **0 hard constraint violations**; status PENDING_APPROVAL, model energy-dispatch-deterministic:2.1.0

For context, across July 2026 the fleet accepted **100 of 116** recommendations - adoption 0.862 against a 0.70 target - for **11,431 t** of expected CO₂ avoided and zero constraint violations.

The furnace inspection carries more value still, but it is not a recommendation you approve: it protects the €8M unplanned-failure case through a maintenance window.""",
    # -- operations --------------------------------------------------------
    "operations-q1": """Just short of target. Throughput is **128.4 t/h** against a **130 t/h** target - 1.6 t/h under, though **+3.2%** on the previous period.

- OEE **84.1%** against 85%
- On-time delivery **96.4%** against 97%
- Energy intensity **€312/t** against €300/t, improving 4.1%

The throughput profile dips about **6 t/h between 17:00 and 20:00**. That dip is deliberate: it is reheat load being shifted out of the €280/MWh evening scarcity window. Outside those three hours the line runs at or above target.""",
    "operations-q2": """**LUX-RHF-01**, the reheat furnace, during the 17:00-20:00 window.

- Throughput falls from about 130 t/h to **114-122 t/h** across those three hours
- REHEAT-BATCH-06 (NS-AUTO-HSLA420, 120 t) was moved from 18:45 to **16:45** to avoid the €280/MWh slot
- Downstream, LUX-HSM-01 carries the DP780 coiling drift on COIL-LUX-260725-017

At the other sites: BE-HSM-01 stand F4 is running **5.8% high on roll force**, and ES-RHF-01 burner zone 02 is **4% rich on air/fuel**, worth about 180 kWh/h of avoidable loss.

The line genealogy is LUX-BF-01 to LUX-BOF-01 to LUX-CC-01 to LUX-RHF-01 to LUX-HSM-01, so the reheat hold is what the mill sees as lost hours - not a mill fault.""",
    "operations-q3": """**Shift handover - Crew A (06:00-14:00, A. Weber) to Crew B (14:00-22:00, M. Dupont). Handover 13:45; Crew C takes over at 22:00.**

Production: throughput **128.4 t/h** against 130, OEE **84.1%** against 85%, on-time **96.4%** against 97%, energy intensity **€312/t** against 300.

Open incidents - 16 alerts: 1 critical, 8 warning, 7 info, 2 acknowledged.
- CRITICAL ALERT-HEARTH-SECTOR-07-260725 - LUX-BF-01, RUL P50 19.65 days, risk 0.90
- WARNING ALERT-ENERGY-SCARCITY-1830 - €280/MWh between 18:30 and 19:00
- WARNING ALERT-QUALITY-DRIFT-DP780 - COIL-LUX-260725-017, acknowledged at 04:00
- WARNING ALERT-ETS-ALLOWANCE-Q3 - allowance headroom 6.2%

Open items and decisions:
- WO-DEMO-LUX-1042, planned inspection on HEARTH-SECTOR-07, raised 18:00
- REC-DEMO-LUX-240725 dispatch still PENDING_APPROVAL - €2,688.70, 7.25%
- 5 decision records AUD-0001 to AUD-0005, all with complete traceability""",
    "operations-q4": """The hearth prediction on **LUX-BF-01** should go up.

- ALERT-HEARTH-SECTOR-07-260725, CRITICAL, open since 17:58
- RUL **P50 19.65 days** (P10 18.69 / P90 20.61), risk **0.90**
- Lining at **363 mm** against a 300 mm safe minimum, thinning about **3.0 mm/day**
- It needs a reline window inside **18-24 days**, which is a production-plan decision rather than a maintenance one

Second on the list is Q3 ETS headroom at **6.2%** - a commercial exposure at €86/t rather than an operational one. Everything else on the board is inside normal shift triage.""",
    # -- furnace-health ----------------------------------------------------
    "furnace-health-q1": """The thermal signature is the pattern five hearth sectors make when you watch them together rather than one at a time.

- SECTOR-05, -06, -08 and -09 drift at **0.4 °C/h** from 640-664 °C
- **SECTOR-07 rises at 3.4 °C/h** from 652 °C and crosses the **700 °C** anomaly threshold around hour 14; cells at 720 °C or above are flagged critical
- Cooling looks unremarkable - delta T **9.4 °C** at **198 m³/h** - which is exactly what makes the sector divergence meaningful rather than a cooling fault
- Heat flux **118 kW/m²**, cooling-water heat proxy **214.7 kW**, apparent thermal resistance **8.73**
- The refractory estimate on the sector falls from **372.0 mm to 363 mm** across the 24-hour window

Model **lining-rul-piml/1.3.0-demo** turns that into remaining life, weighting heat_flux_6h_slope 29%, sector_to_ring_temp_delta 24% and cooling_efficiency_residual 18%.""",
    "furnace-health-q2": """**HIGH - risk score 0.8995 (90%)** on component HEARTH-SECTOR-07.

- Remaining useful life **P50 19.65 days**, P10 18.69, P90 20.61 - a tight band
- Lining thickness **363 mm** against an estimated **300 mm** minimum, degrading about 3.0 mm/day
- Model lining-rul-piml/1.3.0-demo, scored at 18:45 today
- The second unit, **LUX-RHF-01**, sits at 34% risk with about 120 days left - WATCH, not action

The programme target (KPI-FUR-01) is at least **21 days** of advance warning. In the July 2026 history every alert episode fired at exactly **21.0 days** - BE-EAF-01 on 2026-06-19 for a 2026-07-10 failure date, LUX-RHF-01 on 2026-06-09 for 2026-06-30 - and unplanned_outage_flag was **false on every row**.""",
    "furnace-health-q3": """Three drivers carry 71% of the score.

- **heat_flux_6h_slope - 29%.** Local heat flux at 118 kW/m² with a rising six-hour slope: heat is reaching the shell faster than an intact lining allows.
- **sector_to_ring_temp_delta - 24%.** SECTOR-07 climbs at 3.4 °C/h while its neighbours drift at 0.4 °C/h. The divergence, not the absolute temperature, is the signal.
- **cooling_efficiency_residual - 18%.** Cooling delta T of 9.4 °C at 198 m³/h removes less heat than the flow implies, so apparent thermal resistance has fallen to 8.73.

The remaining 29% is spread across slower features. Thickness now reads **363 mm** against a 300 mm minimum, and at about 3.0 mm/day that is what fixes the P50 at **19.65 days**.""",
    "furnace-health-q4": """**WO-DEMO-LUX-1042 - planned inspection, HEARTH-SECTOR-07, LUX-BF-01.**

Rationale: the physics-informed lining model (lining-rul-piml/1.3.0-demo) scores sector 07 at **risk 0.8995** with **RUL P50 19.65 days** (P10 18.69 / P90 20.61). Estimated thickness is **363 mm** against a **300 mm** safe minimum and falling about **3.0 mm/day**. The drivers are a rising six-hour heat-flux slope (29%), a sector-to-ring temperature delta of 3.4 °C/h against 0.4 °C/h on neighbouring sectors (24%), and a cooling-efficiency residual (18%). Cooling flow is nominal at 198 m³/h with delta T 9.4 °C, so a cooling fault does not explain the signal.

Scope: verify shell thermocouples against neighbouring sectors, record cooling inlet and outlet delta T with recent flow history, and confirm the thickness estimate before the reline window opens. **PROC-DEMO-0002** (cooling-circuit inspection and ultrasound escalation, approved v3) applies; **PROC-DEMO-0001** (hearth sector over-temperature verification) is still in review.

Schedule: inspection days 1-4, ultrasound days 5-8, reline window **days 18-24**. Acting inside that window is what keeps this a planned event - in the July 2026 history every alert episode ended in a planned reline with unplanned_outage_flag false.""",
    # -- energy-optimization -----------------------------------------------
    "energy-optimization-q1": """**REC-DEMO-LUX-240725** - move flexible reheat out of the evening scarcity window.

- Baseline **€37,109.10** to optimized **€34,420.40**, a saving of **€2,688.70 (7.25%)**
- Peak demand **56.0 MW to 51.58 MW**, down 7.89%; shiftable load 18 MW
- The move that pays: REHEAT-BATCH-06 out of slot 75 (18:45, **€280.00/MWh**, €3,920.00) into slot 67 (16:45, €97.24/MWh, **€1,361.36**)
- Tonnage unchanged at **960 t** across 8 batches of 120 t / 14 MWh on LUX-RHF-01
- **0 hard constraint violations**; status PENDING_APPROVAL, model energy-dispatch-deterministic:2.1.0

REHEAT-BATCH-03 stays fixed at 09:45 because it is flagged urgent. Two batches are pulled forward 15-30 minutes, and batches 00 and 07 move into cheaper night slots.""",
    "energy-optimization-q2": """Because one slot costs more than most of the rest of the day put together.

- The day-ahead curve peaks at **€280.00/MWh at 18:45**, against 54.85-€112.64/MWh everywhere else
- Reheating a single 120 t / 14 MWh batch in that slot costs **€3,920.00**; the same batch at 16:45 (€97.24/MWh) costs **€1,361.36** - a €2,558.64 difference from one batch
- Scarcity runs **17:00-20:00**, which is also where the operations throughput profile shows its 6 t/h dip
- A wind PPA surplus of **12 MWh** is forecast for 02:00-05:00, which is why batch 07 moves to 23:30 and batch 00 to 02:15

Total flexible-batch cost falls from €12,369.70 to €9,681.00. The fixed plant load of €24,739.40 is priced identically in both schedules, so the entire **€2,688.70** saving comes from the eight reheat batches.""",
    "energy-optimization-q3": """All five constraints report SATISFIED, with **0 hard violations**.

- **equal_planned_tonnage** - 960.00 t planned, 960.00 t scheduled. The optimizer may move steel, never remove it.
- **urgent_batch_fixed** - REHEAT-BATCH-03 (NS-AUTO-HSLA420, urgent) stays in slot 39 at 09:45, unshifted.
- **minimum_soak_time** - 60 minutes of soak preserved on every batch.
- **maximum_hold_time** - no batch held beyond the 120-minute limit; the largest move is batch 06 at -120 minutes.
- **equipment_capacity** - at most 2 concurrent batches on LUX-RHF-01.

That is what makes the result approvable: the **€2,688.70** saving is produced entirely inside the constraint set, and the recommendation is versioned (v1) and auditable as **AUD-0002**.""",
    "energy-optimization-q4": """**Down 3.29%** on this dispatch - achieved by moving load into cleaner slots, not by producing less.

- Grid carbon intensity averages about **244 gCO₂/kWh** across the 96 quarter-hour slots, swinging roughly between 140 and 310
- Tonnage is unchanged at **960 t**, so the reduction is pure carbon arbitrage
- Peak demand also falls **56.0 to 51.58 MW**, which is where scarcity-hour carbon usually sits
- The modelled full-plan dispatch reduction on the sustainability summary is **8.7%**

At fleet scale in July 2026, the **100 accepted** recommendations (of 116, adoption 0.862 against a 0.70 target) carry **11,431 t** of expected CO₂ avoided.""",
    # -- quality -----------------------------------------------------------
    "quality-q1": """**COIL-LUX-260725-017**, grade NS-AUTO-DP780 - the only batch currently at FAIL.

- Risk score **0.429**, characteristic YIELD_STRENGTH
- Coiling temperature bias **+11.4 °C**, the largest on the board; the next highest is +3.0 °C
- Measured yield strength **452.4 MPa** against a 380-520 MPa spec - inside spec, but the lab result is in REVIEW
- Source heat H-LUX-260725-0040, mill LUX-HSM-01
- ALERT-QUALITY-DRIFT-DP780 was acknowledged at 04:00 and is still open

Of the 20 batches on the board this is the one an automotive customer would see. The drift was flagged before the first off-spec lab result, which is the point of the signal.""",
    "quality-q2": """One point is out of control, and it is the most recent one.

- Mean **1.9**, sigma **2.2**, so UCL **8.5** and LCL **-4.7**
- Subgroup 20 reads **11.4** - above the upper control limit, and the same **+11.4 °C** coiling bias carried by COIL-LUX-260725-017
- Subgroups 1-19 stay inside the limits, peaking at 5.8. There is no run, trend or limit-hugging pattern before it
- Process capability **Cpk 1.18** against a **1.33** target - capable, but not comfortably

Over 30 days there are **86 defects**, and coiling temperature drift accounts for **34 of them (39.5%)**, ahead of edge crack (21), surface scale (14), thickness variance (9), coating porosity (5) and other (3). A single special-cause point on the dominant defect family points to an assignable cause, not to re-centring the process.""",
    "quality-q3": """The chain behind COIL-LUX-260725-017 is intact end to end, which is what lets the deviation be placed.

- Raw material lot LOT-FE-017 to heat **H-LUX-260725-0040** to ladle treatment LADLE-017 to slab SLAB-017
- Reheat at **LUX-RHF-01** (REHEAT-017) to coil COIL-LUX-260725-017 to sample SMP-017 to test YIELD_STRENGTH **452.4 MPa** (REVIEW) to shipment SHIP-DEMO-017
- Carbon equivalent 0.420 at the head of the sequence, rising 0.002 per batch

The step that moved is the reheat: that furnace was holding batches out of the 17:00-20:00 scarcity window, and the coiling bias came out at **+11.4 °C**. The deviation therefore attaches to the reheat and coiling steps, not to the melt - nothing upstream of the ladle shows a matching signal.""",
    "quality-q4": """Coiling temperature **-8 °C** with rolling force **-3%** - the bounded what-if this screen already runs.

- Predicted first-pass yield moves from about **88% to about 95%**, against scenario bounds of below 0.90 before and at least 0.93 after
- Model **quality-yield-gbm/2.1.0-demo**; the run is recorded as audit **AUD-0003**
- It stays inside spec: yield strength 452.4 MPa sits mid-band in the 380-520 MPa window, so removing the +11.4 °C bias does not threaten the low side
- On the board today, high-grade yield is 94.8% against a 95% target and first-pass yield 97.1% against 97%

Against the programme KPI, July 2026 high-grade first-pass yield was **0.9494** against the **0.972** target - the one outcome still short, by about 2.3 points. Losses that month were 4,498 t downgraded, 8,996 t reworked and 1,499 t scrapped across 464 defects.""",
    # -- sustainability-compliance -----------------------------------------
    "sustainability-compliance-q1": """**71% of allowances used**, with Q3 headroom down to **6.2%**.

- Allowance price **€86.00/t**
- Period exposure forecast **€248,000** at the current emission intensity
- Scope 1 runs at **1,368 t CO₂e/day** for 960 t of steel; Scope 2 follows the grid, averaging about 244 gCO₂/kWh across the 96 intervals
- CO₂ per tonne of steel **1.42 t/t** against a **1.35** target
- ALERT-ETS-ALLOWANCE-Q3 is open on the ledger

For the last month with closed books, July 2026: CO₂ intensity **1.019 tCO₂e/t** against a 1.638 target and a 2.10 baseline, so KPI-CO₂-01 is met - with Scope 1 **355,336 t**, Scope 2 **147,868 t** and total ETS exposure of **€3,974,153**.""",
    "sustainability-compliance-q2": """**In month 5**, on the current trajectory.

- Consumption stands at **71%** and the projection adds about **3.1 points per month**
- Month 4 lands at 83.4% - still under the **85%** guidance threshold
- Month 5 lands at **86.5%**, which is the crossing
- The 100% cap is not reached until about month 10, so the guidance breach comes first by roughly five months
- Q3 headroom is already down to **6.2%**, which is what ALERT-ETS-ALLOWANCE-Q3 is tracking

Accepting the current dispatch moves the line: **-3.29%** CO₂ on that schedule, and a modelled **8.7%** reduction if dispatch optimization runs across the whole plan.""",
    "sustainability-compliance-q3": """Both sit in the same append-only ledger, but they answer different questions.

- **Scope 1 - direct.** Combustion and process emissions on site: **1,368 t CO₂e** for 960 t of steel today, effectively 1,425 kg per tonne. It moves when the process changes, and it does not care what the grid is doing.
- **Scope 2 - indirect, purchased electricity.** Computed per quarter-hour: consumption in the interval times the grid carbon intensity of that same interval - about **244 gCO₂/kWh** on average, ranging roughly 40-480 across the day. It moves when you shift load in time, even at identical tonnage.

That is why the dispatch recommendation reduces CO₂ by **3.29%** without producing less steel: it only touches Scope 2. The ledger holds **96 immutable interval rows**, and ETS exposure is derived from their sum at €86/t.

In July 2026 the split was Scope 1 **355,336 t** and Scope 2 **147,868 t**.""",
    "sustainability-compliance-q4": """Approve the dispatch - it is the only lever that acts today.

- **REC-DEMO-LUX-240725** - CO₂ **-3.29%** immediately, at unchanged tonnage (960 t), 0 hard constraint violations, still PENDING_APPROVAL
- Running dispatch optimization across the whole plan is modelled at **8.7%**
- Next fastest: ES-RHF-01 burner zone 02 is **4% rich on air/fuel**, worth about 180 kWh/h of avoidable loss
- Slowest but largest: the Scope 1 process route itself, which no schedule change reaches

At **€86/t** and with headroom at 6.2%, the dispatch is what keeps the guidance-threshold crossing from moving earlier than month 5. In July 2026 the 100 accepted recommendations carried **11,431 t** of expected CO₂ avoided.""",
    # -- knowledge-hub -----------------------------------------------------
    "knowledge-hub-q1": """**PROC-DEMO-0002 - cooling-circuit inspection and ultrasound escalation.** Status APPROVED, version 3, captured in session SESS-DEMO-015 and cited to transcript:SESS-DEMO-015#seg-2. It is the one approved procedure in the library, and it is the one that applies to the open hearth alert.

Closest neighbour, not yet usable: **PROC-DEMO-0001 - hearth sector over-temperature verification**, version 2, IN_REVIEW, cited to transcript:SESS-DEMO-014#seg-4 and #seg-7. It says to compare neighbouring shell thermocouples before acting, to read cooling inlet and outlet delta T with recent flow history rather than current flow alone, and never to bypass alarms or change controls on the strength of interview guidance.

Grounded answers are drawn from approved procedures only, so PROC-DEMO-0001 can be read but will not be cited as an answer until an expert signs it off.""",
    "knowledge-hub-q2": """**Energy and utilities is the gap - 58% coverage**, the lowest of the five domains.

- Blast furnace **82%**
- Quality lab **77%**
- Hot strip mill **71%**
- Reheat furnace **64%**
- Energy and utilities **58%**

Three captured procedures are past the 5-day review SLA (ALERT-KNOWLEDGE-REVIEW-QUEUE), and only one of the three procedures in the library is approved - so usable coverage is lower than captured coverage in every domain.

The gap bites hardest where the retirements are: the hearth expertise behind PROC-DEMO-0001 is captured but unapproved, while the energy domain - the one carrying the €2,688.70/day dispatch decision - has the least captured to begin with.""",
    "knowledge-hub-q3": """Two of the three procedures are not yet usable.

- **PROC-DEMO-0001 - hearth sector over-temperature verification.** IN_REVIEW, version 2, session SESS-DEMO-014, two cited transcript segments (#seg-4, #seg-7). Directly relevant to the open LUX-BF-01 alert.
- **PROC-DEMO-0003 - reheat furnace zone soak recovery.** DRAFT, version 1, session SESS-DEMO-016, one cited segment (#seg-1).
- Already approved: **PROC-DEMO-0002**, version 3, cooling-circuit inspection and ultrasound escalation.

**ALERT-KNOWLEDGE-REVIEW-QUEUE** flags three captured procedures beyond the 5-day review SLA. Approval is a human step by design: the approval of PROC-DEMO-0002 is recorded as audit **AUD-0004** with actor ke-demo at 10:15, so the chain from operator transcript to published procedure stays auditable.""",
    "knowledge-hub-q4": """Interview guide, grounded on PROC-DEMO-0001 and the current LUX-BF-01 signature. Subject **OP-DEMO-014**, senior blast furnace operator; capture is consent-bound and the transcript is retained under that consent scope.

- When a hearth sector warms but cooling flow reads normal, what do you check first, and in what order?
- Which neighbouring shell thermocouples do you compare against, and how large a delta makes you act? SECTOR-07 is currently rising at 3.4 °C/h against 0.4 °C/h on its neighbours.
- How do you tell lining degradation from a drifting sensor? PROC-DEMO-0001 cites persistence across taps and slower post-tap cooling - what else do you use?
- What do cooling inlet and outlet delta T plus recent flow history tell you that current flow alone does not? Today it reads 9.4 °C at 198 m³/h.
- At an estimated 363 mm of thickness against a 300 mm minimum, what would make you bring the reline window forward?
- What has gone wrong on this furnace before that a new operator would not expect?

Safety boundary to restate on the record: never bypass alarms or change furnace or cooling controls on the strength of interview guidance.""",
    # -- executive-overview ------------------------------------------------
    "executive-overview-q1": """Three of the four target outcomes are met, one is short. Figures are the July 2026 close on the gold tables.

- **Energy intensity (KPI-ENE-01)** - **10.63 GJ/t** against a 16.77 target, from a 19.5 baseline. **Met**, with energy cost around €46.5M against a €54.1M baseline.
- **CO₂ intensity (KPI-CO₂-01)** - **1.019 tCO₂e/t** against a 1.638 target, from a 2.10 baseline. **Met**.
- **Lining advance warning (KPI-FUR-01)** - every alert episode fired at exactly **21.0 days**, the stated minimum, with unplanned_outage_flag false on every row. **Met**.
- **High-grade first-pass yield (KPI-QUA-01)** - **0.9494** against a 0.972 target, from a 0.90 baseline. **Not met**, about 2.3 points short.
- Supporting: dispatch adoption **0.862** (100 of 116 accepted) against a 0.70 minimum. **Met**.

The progress bars on this screen read 92, 88, 96 and 100 out of 100 for energy, CO₂, yield and warning time. Quality is the honest gap, and it is where the knowledge-capture work points next.""",
    "executive-overview-q2": """**Saarbrucken (DE)** on performance, **Moselle (LU)** on risk.

- Moselle (LU) - energy -14.2%, CO₂ -22.4%, yield +8.1%, **3 open alerts** including the only critical one
- Saarbrucken (DE) - energy **-11.8%**, CO₂ **-18.6%**, yield **+6.4%**, 2 open alerts: last on all three measures
- Liege (BE) - energy -13.1%, CO₂ -20.2%, yield +7.2%, 1 open alert
- Asturias (ES) - energy -12.5%, CO₂ -19.4%, yield +7.9%, 2 open alerts

Saarbrucken is the only site below programme target on all three axes, and its open items are cost-shaped: caster mould-level oscillation above the 4.5 mm band, and a scrap charge mix 3.1% above the least-cost recipe.

Moselle leads on every axis but carries the LUX-BF-01 hearth prediction - risk 0.90, 19.65 days - which is the €8M question this week.""",
    "executive-overview-q3": """Four committed outcomes, measured on a synthetic pilot dataset, stated as targets where they are targets.

- **Targets** - energy per tonne -14%, CO₂ per tonne -22%, high-grade yield +8%, at least 21 days of lining warning.
- **Measured in the pilot data** - energy intensity 10.63 GJ/t and CO₂ intensity 1.019 tCO₂e/t in July 2026; every lining alert issued at exactly 21.0 days with no unplanned outage; high-grade first-pass yield 0.9494, still short of the 0.972 target.
- **Measured on a single dispatch today** - €2,688.70 saved (7.25%), peak demand -7.89%, CO₂ -3.29%, zero constraint violations.
- **Modelled, not realised** - one failure prevented, valued in the use case at €8M per unplanned hearth failure.

Governance carries the same weight as the numbers: five decision records across five domains, three of them model-linked, 100% immutability, and every recommendation requiring a human decision before it acts.""",
    "executive-overview-q4": """The separation is clean, and the tiles say so in their tooltips.

**Targets, not measurements:** energy per tonne -14%, CO₂ per tonne -22%, high-grade yield +8%, at least 21 days of advance warning. These are the fleet-wide use-case commitments.

**Measured in this demo:**
- Dispatch - **€2,688.70 (7.25%)** saved, peak 56.0 to 51.58 MW, CO₂ **-3.29%**, 0 hard violations
- Furnace - risk 0.8995 with **P50 19.65 days** of warning on LUX-BF-01, below the 21-day target on this single live episode
- Quality what-if - predicted first-pass yield about 88% to about 95%, model quality-yield-gbm/2.1.0-demo
- July 2026 gold close - 10.63 GJ/t, 1.019 tCO₂e/t, 21.0-day warning at every episode, 0.9494 high-grade first-pass yield

**Modelled:** the €8M avoided-failure value and the single failure-prevented count.

The one number never to present as achieved is the CO₂ target: the fleet target is -22%, while this single-site demo measures -3.29% on one dispatch.""",
    # -- platform-ops ------------------------------------------------------
    "platform-ops-q1": """**Running** - capacity **cap-novasteel-demo-sc**, SKU **F2**, region Sweden Central, environment demo.

- Resumed this morning: Paused to Resuming at 07:27, Resuming to ReadinessCheck at 07:28, ReadinessCheck to Running at 07:30 - all by demo-platform-ops with reason "rehearsal"
- Lifecycle policy: nightly pause check at **01:00 Europe/Luxembourg**
- SKU is switchable between F2, F4 and F8; the state change is recorded as audit **AUD-0005**
- Workspace NovaSteelV3-Demo carries the lakehouse lh_novasteelv3_core, the KQL database kql-ns-operations and the ontology onto_novasteelv3

This is a non-production capacity, and the lifecycle is deliberately restricted to start, pause and SKU change - each one audited.""",
    "platform-ops-q2": """**None failed.** Four of the five most recent runs succeeded and one is still in flight.

- RUN-4821 bronze-to-silver - SUCCEEDED, 17:45, **214 s**
- RUN-4820 silver-to-gold - SUCCEEDED, 17:30, **176 s**
- RUN-4819 semantic-refresh - **RUNNING**, started 18:40, 62 s so far
- RUN-4818 contract-assertions - SUCCEEDED, 17:10, 41 s
- RUN-4817 quarantine-negative-tests - SUCCEEDED, 16:55, 33 s

Both guard jobs passed: contract assertions on the event envelopes, and the negative tests that prove bad payloads land in quarantine instead of silver. End-to-end freshness is **12 s**. The only open item is the semantic refresh.""",
    "platform-ops-q3": """Steady, and small - this is an F2 carrying a demo workload.

- Cost per hour **€2.80**, oscillating about €0.40 either side across the 06:00-18:00 window
- Utilization averages about **38%**, following a smooth profile between roughly 26% and 50%
- Spend to date is the sum of the 13 hourly points on the trend
- Telemetry freshness **12 s**

The shape matters more than the total: utilization peaks alongside the silver-to-gold and semantic-refresh runs, which is why the nightly pause check at 01:00 costs nothing in throughput. On an F2 the capacity itself is the floor of the bill, so pausing between demos is the only real lever.""",
    "platform-ops-q4": """**Not yet - RUN-4819 (semantic-refresh) is still running**, 62 s in, started at 18:40.

- The other four runs have completed: bronze-to-silver, silver-to-gold, contract-assertions and quarantine-negative-tests all SUCCEEDED between 16:55 and 17:45
- Pausing during a semantic-model refresh leaves the model unrefreshed, so dashboards would serve the previous gold snapshot on resume
- Capacity **cap-novasteel-demo-sc** is F2, Running since 07:30, environment demo
- The lifecycle policy already runs its pause check at **01:00 Europe/Luxembourg**, by which time this run is long finished

Wait for RUN-4819 to report SUCCEEDED, then pause. The transition is recorded like the others, with actor and reason.""",
    # -- device-operations -------------------------------------------------
    "device-operations-q1": """**None.** All **17 devices** are reporting and there are **0 active incidents** injected.

- Fleet: 6 in Luxembourg (LUX-BF-01, LUX-BOF-01, LUX-CC-01, LUX-RHF-01, LUX-HSM-01, LUX-UTIL-01), 4 in Germany, 4 in Belgium, 3 in Spain
- **91 sensor signals** online across the fleet
- Uptime ranges **99.10% to 99.95%** per device
- Simulator: scenario **demo-full**, seed 240726, tick 720, about 6 elapsed hours at 5 s per tick

The only device carrying an open alert is **LUX-BF-01** - the hearth prediction - and that is a process condition, not a device fault: its thermocouples, heat-flux and cooling signals are all publishing on schedule. Health on this screen is measured from signal freshness and alarm counts, so a healthy gateway can sit behind a critical process alert.""",
    "device-operations-q2": """It measures gateway health, not process health. Three inputs:

- **Uptime** - the share of the window in which the device published at all. The fleet sits between **99.10% and 99.95%**.
- **Signal freshness** - every signal has an expected emission period and goes stale once it exceeds it. Periods run from **1 s** (arc_current on DE-EAF-01) and 5 s (hearth_shell_temperature, local_heat_flux) up to **900 s** (hearth_refractory_estimate, spot_price, grid_carbon_intensity). One signal is event-driven with no period at all: hot_metal_temperature, emitted only at a tap.
- **Alarm count** - active device alarms in the window, weighted by severity.

A device is healthy when all three hold, degraded when freshness or alarms slip, and faulted when it stops publishing. At tick 720 with no incident injected, all **17 devices and 91 signals** are healthy - which is why the LUX-BF-01 process alert sits beside a clean device score.""",
    "device-operations-q3": """**None are stale right now** - all **91 signals** are inside their expected period at tick 720.

Staleness is judged per signal, and the periods differ widely:
- **1-5 s** - arc_current (DE-EAF-01), hearth_shell_temperature and local_heat_flux (LUX-BF-01), zinc_bath_temperature (BE-GAL-01)
- **10 s** - bath_temperature on LUX-BOF-01 and DE-EAF-01
- **60 s** - production_rate
- **900 s** - hearth_refractory_estimate, spot_price, grid_carbon_intensity
- **Event-driven** - hot_metal_temperature, emitted only at a tap

It matters because a model is only as current as its slowest input. The lining score depends on hearth_refractory_estimate and local_heat_flux: if the 900 s refractory estimate goes stale, the **RUL P50 of 19.65 days** stops moving while the furnace keeps thinning at about 3.0 mm/day. The dispatch has the same exposure through spot_price and grid_carbon_intensity, both also on 900 s.""",
    "device-operations-q4": """Two ways, depending on how long you want it to run.

**Single incident - degrading-furnace.** Severity high, default duration **30 minutes**, target **LUX-BF-01**, driving local_heat_flux, hearth_refractory_estimate and hearth_shell_temperature. Pick it in the incident panel on this screen, confirm the device and duration, and inject.

**Whole scenario - lining-degradation-21d.** Restart the simulator on that scenario instead of demo-full to play the full degradation arc rather than a 30-minute excursion.

- Current state: scenario **demo-full**, seed **240726**, tick 720, about 6 elapsed hours, 5 s ticks, **0 active incidents**
- Other scenarios available: healthy-baseline, energy-price-spike, quality-drift, edge-outage-recovery
- Other incidents: cooling-water-loss (critical, 15 min), sensor-drift (60 min), sensor-dropout (10 min), energy-price-spike (45 min, LUX-UTIL-01), quality-drift (45 min, LUX-CC-01 and LUX-HSM-01), edge-outage-recovery (20 min)

Expect the effect on Furnace Health within a couple of ticks: risk score above 0.80 and RUL P50 landing between **19 and 23 days**, which is the band the scenario is bounded to.""",
    # -- dashboards --------------------------------------------------------
    "dashboards-q1": """**Morning shift handover** - Plant Manager, about **6 minutes**, tagged daily and triage.

It walks Command Center, then Operations, then the open alerts - which is the order a handover actually needs: what is critical, what the line did, what is still open.

What it would show you right now: **16 open alerts** (1 critical, 8 warning, 7 info, 2 acknowledged), throughput **128.4 t/h** against 130, OEE **84.1%**, and one work order - WO-DEMO-LUX-1042 - raised against the hearth prediction.

If the handover is specifically about the furnace, use **Furnace risk investigation** (about 8 minutes) instead; it is the deeper of the two.""",
    "dashboards-q2": """**Compliance evidence pack** - Sustainability Officer and Auditor, about **7 minutes**, tagged compliance, audit and eu-ai-act.

It assembles the evidence trail rather than the metrics:
- **5 decision records**, AUD-0001 to AUD-0005, covering all **5 domains**: furnace, energy, quality, knowledge and capacity
- **3 of them model-linked** - lining-rul-piml/1.3.0-demo, energy-dispatch-milp/1.2.0-demo and quality-yield-gbm/2.1.0-demo
- **100% immutability**, with correlation id run-demo-full-240725 tying the furnace, energy and quality decisions to a single run
- The emissions ledger behind them: 96 append-only interval rows, Scope 1 and Scope 2 separated, ETS priced at €86/t
- Human decision points: every recommendation carries an actor and a timestamp, which is what the EU AI Act traceability argument rests on

That is the pack: what was decided, by which model version, on which data, and approved by whom.""",
    "dashboards-q3": """Six collections, each a fixed route through screens that already exist.

- **Morning shift handover** - Plant Manager, about 6 min, daily and triage. What is critical, what the line did, what is still open.
- **Furnace risk investigation** - Maintenance and Reliability Engineer, about 8 min, reliability and root-cause. Is the lining risk real, what is driving it, when must we act.
- **Energy and cost review** - Energy Manager, about 7 min, energy and cost. What the schedule costs, what the alternative saves, what constrains it.
- **Quality escape review** - Quality Engineer, about 6 min, quality and root-cause. Which batch, which step, what adjustment.
- **Compliance evidence pack** - Sustainability Officer and Auditor, about 7 min, compliance, audit and eu-ai-act. What was decided, by which model, approved by whom.
- **Platform health and spend** - Platform Ops, about 5 min, platform and cost. Is the pipeline healthy, what is it costing.

Each holds three or four ordered screens and adds no data of its own - the numbers stay owned by the screens it links to.""",
    "dashboards-q4": """**Furnace risk investigation** - Maintenance and Reliability Engineer, about **8 minutes**, tagged reliability and root-cause. It runs lining forecast, then thermal explorer, then maintenance planner - the order in which the evidence builds.

What it would show you right now:
- Lining forecast - LUX-BF-01 / HEARTH-SECTOR-07 at risk **0.8995**, RUL **P50 19.65 days** (P10 18.69 / P90 20.61)
- Thermal explorer - SECTOR-07 climbing at **3.4 °C/h** against 0.4 °C/h on its neighbours, crossing the 700 °C anomaly threshold
- Maintenance planner - **WO-DEMO-LUX-1042** open on the sector, reline window at days 18-24

For the wider handover use Morning shift handover (about 6 min); for the audit framing rather than the engineering, Compliance evidence pack carries the decision trail behind the same call.""",
}
