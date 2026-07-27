import type { HelpCatalog } from '../components/help/helpTypes'

/**
 * Explanations for the Help Assistant.
 *
 * House style: assume the reader has never seen a steel plant and has never
 * used this portal. Two short sentences per field, no acronym without its
 * expansion, no marketing. `steel` teaches the process, `useIt` teaches the
 * screen.
 */
export const HELP_EN: HelpCatalog = {
  // ---------------------------------------------------------------- generic
  'generic.kpi': {
    title: 'Headline number',
    what: 'A tile showing one measurement, its trend arrow and how it compares with the target.',
    steel:
      'A steel plant runs on a handful of numbers. Putting them side by side lets a shift manager see the state of the plant in a few seconds instead of reading reports.',
    useIt: 'A tile with an arrow cursor can be clicked to open the detail behind the number.',
  },
  'generic.chart': {
    title: 'Chart',
    what: 'A picture of how a measurement changed over time or how it splits across parts of the plant.',
    steel:
      'Single numbers hide the story. A furnace that averages a safe temperature can still have dangerous spikes, and only a chart shows them.',
    useIt: 'Hover a point for its exact value. Charts in a panel can be enlarged with the maximise button on the tab bar.',
  },
  'generic.table': {
    title: 'Data table',
    what: 'The individual records behind the summary numbers, one per row.',
    steel: 'When a number looks wrong, the table is where you find the specific batch, sensor or work order that caused it.',
    useIt: 'Click a column header to sort, use the header controls to filter, and the search box to find text anywhere in the table.',
  },
  'generic.tableRow': {
    title: 'One record',
    what: 'A single item: one batch, one sensor reading, one work order or one alert.',
    steel: 'Everything that happens in the plant is eventually written down as a record like this, which is what makes an audit possible.',
    useIt: 'Where a row is clickable it opens the full detail of that item.',
  },
  'generic.tableHeader': {
    title: 'Column header',
    what: 'The name of a column, and the control that sorts and filters the table by it.',
    steel: 'Sorting by risk or by date is how an engineer turns a long list into a short list of things to act on today.',
    useIt: 'Click once to sort ascending, again for descending. Filter controls narrow the table to matching rows only.',
  },
  'generic.panel': {
    title: 'Workspace panel',
    what: 'One movable section of the screen. Panels can be dragged by their tab to any edge, resized or stacked.',
    steel: 'Control-room operators all watch different things, so the layout adapts to the person rather than the other way round.',
    useIt: 'Drag the tab to rearrange. Reset layout in the header puts everything back.',
  },
  'generic.dockTab': {
    title: 'Panel tab',
    what: 'The handle of a panel. It names the panel and lets you move it.',
    steel: 'Panels that must always stay visible have no close button, so a critical view cannot be lost by accident.',
    useIt: 'Drag it to move the panel, or click the maximise button to make it fill the workspace.',
  },
  'generic.button': {
    title: 'Action',
    what: 'A control that changes what is shown or asks the platform to do something.',
    steel:
      'Anything that could change plant behaviour is only ever a proposal here. A human still approves it before it reaches the equipment.',
    useIt: 'Hover for a tooltip describing what the action does.',
  },

  // ------------------------------------------------------------ chart types
  'chart.line': {
    title: 'Line chart',
    what: 'Time runs left to right, the measurement runs bottom to top. The line joins consecutive readings.',
    steel: 'Steel processes drift slowly, so the slope matters more than any single reading. A rising line is an early warning.',
    useIt: 'Look for sudden steps and for a slope that keeps going the same way.',
  },
  'chart.area': {
    title: 'Area chart',
    what: 'A line chart with the space under the line filled in, which makes totals easier to compare.',
    steel: 'Useful for quantities that accumulate, such as energy consumed or emissions released over a shift.',
    useIt: 'Compare the size of the filled areas rather than the height of the line.',
  },
  'chart.bar': {
    title: 'Bar chart',
    what: 'One bar per category. Taller means more.',
    steel: 'Good for comparing furnaces, product grades or shifts against each other at a glance.',
    useIt: 'Look for the outlier bar - that is usually where the problem or the opportunity is.',
  },
  'chart.heatmap': {
    title: 'Heat map',
    what: 'A grid where colour stands for a value. Darker or hotter colours mean higher readings.',
    steel:
      'A blast furnace is lined with hundreds of sensors. A heat map shows all of them at once so a hot spot on the shell stands out immediately.',
    useIt: 'Scan for isolated bright cells. One hot cell surrounded by cool ones usually means a local wear problem.',
  },
  'chart.gauge': {
    title: 'Gauge',
    what: 'A dial showing one value against its safe range.',
    steel: 'Mirrors the analogue instruments operators have used on the plant floor for decades, so it needs no explanation on a control screen.',
    useIt: 'The coloured band tells you whether the current value is comfortable, marginal or out of limits.',
  },
  'chart.control': {
    title: 'Control chart',
    what: 'A time chart with a centre line for the target and two outer lines for the acceptable range.',
    steel:
      'This is the classic quality tool. A process that stays inside the outer lines is predictable; a point outside them means something changed and must be investigated.',
    useIt: 'Watch for points outside the limits, and for long runs of points on one side of the centre line.',
  },
  'chart.pareto': {
    title: 'Pareto chart',
    what: 'Bars sorted from largest to smallest, with a rising line showing the running total.',
    steel:
      'Most scrap and rework comes from a small number of causes. Fixing the first two or three bars usually removes most of the loss.',
    useIt: 'Find where the line crosses 80 percent - the bars to its left are your priority list.',
  },
  'chart.donut': {
    title: 'Donut chart',
    what: 'A ring split into slices, each slice a share of the whole.',
    steel: 'Used for breakdowns such as where emissions come from, where a slice is easier to judge than a percentage in a table.',
    useIt: 'Compare slice sizes; hover for the exact share.',
  },
  'chart.gantt': {
    title: 'Schedule bar chart',
    what: 'Each bar is an activity, positioned and sized by when it starts and how long it lasts.',
    steel:
      'Furnace relines and maintenance stops have to fit between production campaigns. Seeing them on one timeline is how planners avoid a clash.',
    useIt: 'Look for overlaps and for gaps that could absorb a maintenance window.',
  },
  'chart.priceLoad': {
    title: 'Price and load chart',
    what: 'Two things on one timeline: the electricity price, and how much power the plant plans to draw.',
    steel:
      'Electricity is one of the largest costs in steelmaking and its price changes every hour. Doing energy-hungry work when the price is low saves real money.',
    useIt: 'Check that the tall load bars sit under the low points of the price line.',
  },
  'chart.bullet': {
    title: 'Progress bar',
    what: 'A bar showing where the current value sits between zero and its target.',
    steel: 'Gives a quick sense of how much of a commitment, such as an annual emissions budget, has already been used.',
    useIt: 'The marker on the bar is the target; the filled part is where you actually are.',
  },
  'chart.sparkline': {
    title: 'Mini trend',
    what: 'A very small line chart with no axes, showing only the recent shape of the measurement.',
    steel: 'Fits inside a headline tile so you get the direction of travel without leaving the summary screen.',
    useIt: 'Read the shape, not the values. Click the tile for the full chart.',
  },

  // ------------------------------------------------------- executive layer
  'kpi:energy': {
    title: 'Energy intensity',
    what: 'Electricity and fuel used to make one tonne of steel, in kilowatt-hours per tonne.',
    steel:
      'Making steel means heating iron ore or scrap to around 1,600 degrees Celsius. Energy is therefore both the biggest cost and the biggest source of emissions.',
    useIt: 'Compare against the target line. A fall here flows straight through to cost and to carbon.',
  },
  'kpi:co2': {
    title: 'Carbon dioxide emissions',
    what: 'Tonnes of CO2 released, or the reduction achieved against the reference period.',
    steel:
      'Steel accounts for roughly seven percent of global CO2. In Europe a plant must surrender an emissions allowance for every tonne it releases, so this number has a price attached.',
    useIt: 'Read it together with energy intensity - most reductions here come from using less or cleaner electricity.',
  },
  'kpi:yield': {
    title: 'High-grade yield',
    what: 'The share of production that meets the premium specification first time.',
    steel:
      'Steel that misses specification is not waste - it is remelted. But remelting spends the energy twice, so yield is really an energy and cost measure in disguise.',
    useIt: 'A drop here usually shows up shortly afterwards in the quality screens.',
  },
  'kpi:warning': {
    title: 'Warning lead time',
    what: 'How many days of notice the models give before a predicted problem would occur.',
    steel:
      'Ordering refractory brick and booking a repair crew takes weeks. A warning that arrives too late is worth nothing, so lead time matters as much as accuracy.',
    useIt: 'The pilot target is at least 21 days. Anything less leaves no time to plan a stop.',
  },
  'kpi:failures': {
    title: 'Unplanned stoppages',
    what: 'Number of times production stopped without being scheduled.',
    steel:
      'An unplanned blast-furnace stop is extremely expensive: the vessel must be kept hot, downstream mills starve, and the restart itself costs energy.',
    useIt: 'The goal of the whole platform is to convert these into planned stops.',
  },

  // ---------------------------------------------------------- furnace health
  'kpi:risk': {
    title: 'Lining risk',
    what: 'A score from 0 to 1 estimating how likely the furnace lining is to reach its wear limit soon.',
    steel:
      'A blast furnace is a steel shell lined with heat-resistant brick called refractory. The brick slowly erodes; if it erodes through, molten metal reaches the shell. This score is the plant\u2019s early warning.',
    useIt: 'Above 0.8 the maintenance planner should be booking a repair window.',
  },
  'kpi:days': {
    title: 'Remaining useful life',
    what: 'Estimated days of operation left before the lining reaches its wear limit, at the current rate.',
    steel:
      'Known in the industry as RUL. Replacing a lining is a multi-week campaign, so knowing the date months ahead is what turns a crisis into a project.',
    useIt: 'Use the confidence figure next to it - a short life with low confidence needs more measurement, not immediate action.',
  },
  'kpi:confidence': {
    title: 'Model confidence',
    what: 'How sure the model is about its own prediction, given the data it had.',
    steel: 'Sensors fail and readings drift. Publishing confidence alongside the answer stops an engineer trusting a number built on thin data.',
    useIt: 'Low confidence is a signal to check sensor health before acting on the prediction.',
  },
  'kpi:failDate': {
    title: 'Projected wear-out date',
    what: 'The calendar date the remaining-life estimate points to.',
    steel: 'Turning "so many days" into a date is what lets planners line it up with holidays, contractor availability and order books.',
    useIt: 'Compare it with the planned maintenance window on the planner screen.',
  },
  'kpi:anomalies': {
    title: 'Thermal anomalies',
    what: 'Number of readings that departed from the expected pattern in the selected window.',
    steel:
      'A local hot spot on the furnace shell is usually the first physical sign that the brick behind it has thinned.',
    useIt: 'Open the heat map to see where on the shell the anomalies are clustered.',
  },
  'kpi:cooling': {
    title: 'Cooling water performance',
    what: 'How effectively the cooling system is removing heat from the furnace shell.',
    steel:
      'Water-cooled staves sit between the brick and the steel shell. If cooling weakens, the shell heats up, so this is a safety measurement, not just an efficiency one.',
    useIt: 'A falling value with rising shell temperature is the combination that matters.',
  },
  'kpi:slope': {
    title: 'Temperature trend',
    what: 'How fast the temperature is rising or falling, in degrees per day.',
    steel: 'Refractory wear is slow, so a persistent upward slope of even a fraction of a degree per day is meaningful.',
    useIt: 'The sign matters more than the size. Sustained positive slope on one sector deserves a look.',
  },
  'kpi:sensor': {
    title: 'Sensor coverage',
    what: 'How many thermal sensors are reporting healthy data right now.',
    steel: 'Predictions are only as good as their inputs. A sector with dead sensors is effectively unmonitored.',
    useIt: 'Cross-check with the device fleet screen when the count drops.',
  },
  'furnace-health/thermal-explorer:kpi:peak': {
    title: 'Peak shell temperature',
    what: 'The highest temperature measured on the furnace shell in the selected period.',
    steel:
      'The shell should stay far cooler than the molten interior. A rising peak means heat is finding a path through the brick lining.',
    useIt: 'Use the heat map to find which sector produced the peak.',
  },
  'kpi:open': {
    title: 'Open work orders',
    what: 'Maintenance jobs raised but not yet completed.',
    steel: 'Steel plants run continuously, so maintenance competes with production for time. The backlog is the visible cost of deferring it.',
    useIt: 'Sort the work-order table by priority to see what should be pulled into the next window.',
  },
  'kpi:urgent': {
    title: 'Urgent work orders',
    what: 'Jobs flagged as needing attention before the next planned stop.',
    steel: 'These are the ones that decide whether the next stop is planned or forced.',
    useIt: 'Anything here should be matched against the maintenance window length.',
  },
  'kpi:completed': {
    title: 'Completed work orders',
    what: 'Jobs closed in the current period.',
    steel: 'Completion rate against the backlog tells you whether maintenance capacity matches the plant\u2019s needs.',
    useIt: 'Read together with the open count - both falling is good, only completed falling is not.',
  },
  'kpi:window': {
    title: 'Maintenance window',
    what: 'The length of the next scheduled production stop available for repairs.',
    steel:
      'Relining part of a furnace can take days and the vessel must cool first. Fitting the work into the window is the planner\u2019s central problem.',
    useIt: 'Compare it with the total duration of the urgent work orders.',
  },

  // ------------------------------------------------------------------ energy
  'kpi:price': {
    title: 'Electricity spot price',
    what: 'What a megawatt-hour of electricity costs on the wholesale market right now.',
    steel:
      'European power prices change every hour and can vary several-fold within a day. A plant that can move flexible load into cheap hours cuts its bill without producing less.',
    useIt: 'Line it up against the planned load on the price and load chart.',
  },
  'kpi:savings': {
    title: 'Projected savings',
    what: 'Money the proposed schedule would save compared with running the same work at a flat rate.',
    steel: 'The saving comes purely from timing. The same tonnes are produced, just at cheaper hours.',
    useIt: 'This is a proposal. It only becomes real once an operator approves the schedule.',
  },
  'kpi:shiftable': {
    title: 'Shiftable load',
    what: 'How much of the plant\u2019s electricity demand can be moved to a different hour.',
    steel:
      'A blast furnace cannot be paused, but reheat furnaces, rolling mills and oxygen plants have some flexibility. Only that flexible part can chase cheap power.',
    useIt: 'It sets the ceiling on what any optimisation can achieve.',
  },
  'kpi:baseline': {
    title: 'Baseline scenario',
    what: 'What the cost and emissions would be with no load shifting at all.',
    steel: 'Every claimed improvement needs something to be measured against. This is that reference.',
    useIt: 'Compare it with the optimised scenario to read the benefit.',
  },
  'kpi:optimized': {
    title: 'Optimised scenario',
    what: 'Cost and emissions under the schedule the optimiser proposes.',
    steel: 'The optimiser respects real plant constraints - minimum run times, ramp rates and grid connection limits - not just price.',
    useIt: 'Check the constraint violations tile before trusting the number.',
  },
  'kpi:estimate': {
    title: 'Scenario estimate',
    what: 'The result of the what-if settings currently selected on this screen.',
    steel: 'Lets a planner test an idea before committing the plant to it.',
    useIt: 'Change the sliders and watch this number react.',
  },
  'kpi:violations': {
    title: 'Constraint violations',
    what: 'How many plant rules the current scenario would break.',
    steel:
      'Constraints encode physical reality: a furnace that must stay above a temperature, a mill that cannot start and stop repeatedly. A cheap schedule that breaks them is not a schedule.',
    useIt: 'This must be zero before a scenario can be proposed for approval.',
  },
  'energy-optimization/load-shift-simulator:kpi:peak': {
    title: 'Peak demand',
    what: 'The highest electricity draw the scenario would reach.',
    steel:
      'Grid connections are billed partly on the highest peak reached, so shaving the peak saves money even when total consumption is unchanged.',
    useIt: 'Watch it while shifting load - moving work can accidentally create a new, higher peak.',
  },
  'kpi:server': {
    title: 'Solver status',
    what: 'Whether the optimisation engine found a valid answer, and how good it is.',
    steel: 'Being honest about whether the maths converged is what separates a decision-support tool from a black box.',
    useIt: 'An infeasible result means the constraints cannot all be met - relax one and rerun.',
  },

  // ----------------------------------------------------------------- quality
  'kpi:firstpass': {
    title: 'First-pass rate',
    what: 'Share of batches that met specification without rework.',
    steel: 'Rework means remelting, which spends energy twice and delays the order. First-pass rate is where quality and cost meet.',
    useIt: 'A fall here should be traceable to a cause on the Pareto chart.',
  },
  'kpi:defect': {
    title: 'Defect rate',
    what: 'Share of production with a recorded defect.',
    steel: 'Typical defects are surface cracks, inclusions of slag, or a chemistry that drifted outside the customer\u2019s range.',
    useIt: 'Use the Pareto chart to find which few defect types dominate.',
  },
  'kpi:ncr': {
    title: 'Non-conformance reports',
    what: 'Formal records raised when a batch did not meet its specification.',
    steel: 'Customers in automotive and construction audit these records, so they are a compliance obligation as well as a quality signal.',
    useIt: 'Open the table to see which product grades are affected.',
  },
  'kpi:cpk': {
    title: 'Process capability (Cpk)',
    what: 'A single number saying how comfortably the process fits inside the customer\u2019s tolerance.',
    steel:
      'Above 1.33 is generally considered capable; below 1.0 means defects are expected as a matter of course rather than by accident.',
    useIt: 'Read it with the control chart - Cpk summarises what the chart shows in detail.',
  },
  'kpi:ooc': {
    title: 'Out-of-control points',
    what: 'Readings that fell outside the statistical limits on the control chart.',
    steel:
      'Out of control does not mean out of specification. It means the process changed, which is a reason to investigate before the customer notices.',
    useIt: 'Each point should have an assigned cause recorded against it.',
  },
  'kpi:total': {
    title: 'Total measurements',
    what: 'How many readings the statistics on this screen are based on.',
    steel: 'Statistical rules need enough data to be meaningful. A capability figure from a handful of samples is not trustworthy.',
    useIt: 'Widen the time range if this count is low.',
  },
  'kpi:top': {
    title: 'Largest contributor',
    what: 'The single category responsible for the biggest share of the problem.',
    steel: 'Improvement programmes succeed by fixing one dominant cause at a time rather than everything at once.',
    useIt: 'This is the first bar on the Pareto chart.',
  },

  // -------------------------------------------------------- sustainability
  'kpi:allowance': {
    title: 'Emissions allowances',
    what: 'Permits held, each of which covers one tonne of CO2.',
    steel:
      'Under the EU Emissions Trading System a plant must surrender one allowance per tonne emitted. Some are granted free, the rest must be bought.',
    useIt: 'Compare with the cap and with actual emissions to see the gap.',
  },
  'kpi:cap': {
    title: 'Allowance cap',
    what: 'The free allocation the plant receives for the compliance year.',
    steel: 'The cap shrinks every year by design, which is the mechanism that forces the sector to decarbonise.',
    useIt: 'Emissions above the cap have to be covered by purchased allowances.',
  },
  'kpi:used': {
    title: 'Allowances used',
    what: 'How much of the allocation has been consumed so far this year.',
    steel: 'Consumption is not even across the year - a cold winter or a long campaign moves it.',
    useIt: 'Compare the percentage used with the percentage of the year elapsed.',
  },
  'kpi:overage': {
    title: 'Projected shortfall',
    what: 'Allowances the plant is forecast to be short by year end.',
    steel: 'A shortfall has to be bought on the market at whatever the carbon price is then, so it is a direct financial exposure.',
    useIt: 'Multiply by the carbon price to see the cost, shown in the exposure tile.',
  },
  'kpi:exposure': {
    title: 'Carbon cost exposure',
    what: 'The money value of the projected allowance shortfall.',
    steel: 'This turns an environmental number into a line the finance director understands, which is what gets decarbonisation funded.',
    useIt: 'It moves with both plant emissions and the market carbon price.',
  },
  'kpi:intensity': {
    title: 'Emissions intensity',
    what: 'CO2 released per tonne of steel produced.',
    steel:
      'Intensity is the fair way to compare plants and years, because total emissions fall simply by producing less. Intensity only falls if the process improves.',
    useIt: 'Use this rather than total tonnes when judging progress.',
  },
  'kpi:target': {
    title: 'Target',
    what: 'The value the plant has committed to reach, shown next to where it actually is.',
    steel: 'Targets in this demo are pilot commitments, not measured results. The measured value is always shown alongside.',
    useIt: 'The gap between the two is what the improvement programme has to close.',
  },
  'kpi:records': {
    title: 'Audit records',
    what: 'How many events have been written to the tamper-evident audit log.',
    steel: 'Regulators and customers both ask how a reported number was produced. Every calculation here leaves a record that answers that.',
    useIt: 'Open the table to inspect individual entries.',
  },
  'kpi:immutable': {
    title: 'Chain integrity',
    what: 'Whether the audit log verifies end to end.',
    steel:
      'Each entry carries a cryptographic fingerprint of the one before it, so altering an old record breaks every fingerprint after it and is immediately visible.',
    useIt: 'Anything other than verified means the log should not be relied on.',
  },
  'kpi:models': {
    title: 'Registered models',
    what: 'How many prediction models are registered with a recorded version.',
    steel: 'If a prediction influenced a decision, you need to know exactly which version of which model produced it.',
    useIt: 'Model version appears alongside every prediction in the audit table.',
  },
  'kpi:domains': {
    title: 'Covered domains',
    what: 'How many areas of the plant are represented in the audit trail.',
    steel: 'Partial coverage is a compliance gap. The aim is that every decision-relevant area writes to the same log.',
    useIt: 'Filter the audit table by domain to inspect one area.',
  },

  // --------------------------------------------------------------- knowledge
  'kpi:sessions': {
    title: 'Capture sessions',
    what: 'Interviews recorded with experienced operators and turned into draft procedures.',
    steel:
      'Much of the know-how in a steel plant lives in the heads of people who have run the furnace for thirty years. Capturing it before they retire is a real industrial problem.',
    useIt: 'Open a session to see the transcript alongside the draft it produced.',
  },
  'kpi:coverage': {
    title: 'Procedure coverage',
    what: 'Share of critical tasks that now have a written, approved procedure.',
    steel: 'Gaps in coverage are where the plant depends on one individual being available.',
    useIt: 'Use it to prioritise which interviews to run next.',
  },
  'kpi:approved': {
    title: 'Approved procedures',
    what: 'Drafts that a qualified human has reviewed and signed off.',
    steel: 'A procedure written by a machine and never checked is a liability. Approval is the control that makes the output usable.',
    useIt: 'Only approved procedures are returned as answers by the assistant.',
  },
  'kpi:review': {
    title: 'Awaiting review',
    what: 'Drafts waiting for a human to accept, correct or reject them.',
    steel: 'This queue is the human-in-the-loop gate. Nothing bypasses it.',
    useIt: 'A growing queue means review capacity, not capture capacity, is the bottleneck.',
  },

  // -------------------------------------------------------------- operations
  'kpi:oee': {
    title: 'Overall equipment effectiveness',
    what: 'One number combining how much of the time equipment ran, how fast it ran and how much of the output was good.',
    steel: 'The standard manufacturing scorecard. It stops a plant claiming success on availability while quietly scrapping product.',
    useIt: 'When it falls, check which of the three parts caused it.',
  },
  'kpi:throughput': {
    title: 'Throughput',
    what: 'Tonnes of steel produced in the period.',
    steel: 'The plant\u2019s output, and the denominator of almost every other measure on this portal.',
    useIt: 'Always read intensity measures against it - low output flatters total emissions.',
  },
  'kpi:ontime': {
    title: 'On-time delivery',
    what: 'Share of customer orders shipped by their promised date.',
    steel: 'Steel goes into scheduled production lines downstream, so a late delivery stops somebody else\u2019s factory.',
    useIt: 'Late deliveries often trace back to unplanned stoppages or rework.',
  },
  'kpi:alerts': {
    title: 'Active alerts',
    what: 'Conditions currently flagged as needing attention.',
    steel: 'Alert fatigue is a genuine safety risk, so this platform aims for few, meaningful alerts rather than many.',
    useIt: 'Click through to see the underlying signal for each alert.',
  },

  // ---------------------------------------------------------- platform ops
  'kpi:util': {
    title: 'Capacity utilisation',
    what: 'How much of the reserved analytics compute capacity is in use.',
    steel: 'The platform runs on a deliberately small, paid-by-the-hour capacity so a demonstration environment does not cost like a production one.',
    useIt: 'Sustained high utilisation is the signal to scale up before jobs start queuing.',
  },
  'kpi:utilization': {
    title: 'Capacity utilisation',
    what: 'How much of the reserved analytics compute capacity is in use.',
    steel: 'Analytics capacity is billed by the hour whether or not it is busy, so idle capacity is pure waste.',
    useIt: 'Use it with the cost tile to judge whether the current size is right.',
  },
  'kpi:spend': {
    title: 'Platform spend',
    what: 'What the analytics platform has cost over the period shown.',
    steel: 'A decision-support system has to cost less than the losses it prevents. Showing the cost openly is part of that argument.',
    useIt: 'Compare with the savings reported on the energy screens.',
  },
  'kpi:cost': {
    title: 'Cost',
    what: 'The money figure for the item shown on this tile.',
    steel: 'Every technical choice on this platform has a price, and it is deliberately visible rather than hidden.',
    useIt: 'Open the cost table for the breakdown by service.',
  },
  'kpi:rate': {
    title: 'Processing rate',
    what: 'How many records the pipeline is handling per unit of time.',
    steel: 'Sensor data arrives continuously. If the pipeline processes more slowly than data arrives, dashboards silently fall behind.',
    useIt: 'Read it with data freshness - a healthy rate but stale data means something upstream stopped.',
  },
  'kpi:fresh': {
    title: 'Data freshness',
    what: 'How long ago the newest data point arrived.',
    steel: 'A control-room screen showing yesterday\u2019s temperatures is worse than no screen at all, because it looks current.',
    useIt: 'If this grows, treat every other number on the portal as suspect until it recovers.',
  },
}
