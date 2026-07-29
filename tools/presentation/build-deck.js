const path = require("path");
const fs = require("fs");
const PptxGenJS = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..", "..");
const OUTPUT = process.env.NOVASTEEL_OUTPUT
  ? path.resolve(process.env.NOVASTEEL_OUTPUT)
  : path.join(ROOT, "docs", "presentation", "NovaSteel-Oral-Defense.pptx");
const SLIDE_LIMIT = Number(process.env.NOVASTEEL_SLIDE_LIMIT || 0);
const ASSETS = path.join(__dirname, "assets");
const W = 13.333;
const H = 7.5;
const BACKUP_SLIDES = 8;

const C = {
  carbon: "121719",
  coal: "1F2426",
  graphite: "465057",
  steel: "AEB9BA",
  mist: "DDE4E1",
  paper: "F4F0E9",
  white: "FFFFFF",
  ink: "202729",
  muted: "687373",
  rust: "B64A2D",
  oxide: "7A261C",
  amber: "E3A72F",
  teal: "147D74",
  green: "6D9A6F",
  red: "B83B35",
  paleRust: "F1DDD4",
  paleAmber: "F3E9CB",
  paleTeal: "D8ECE7",
  paleSteel: "E5E9E6",
};

const F = {
  head: "Bahnschrift SemiBold",
  body: "Aptos",
  mono: "Consolas",
};

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "NOVA_WIDE", width: W, height: H });
pptx.layout = "NOVA_WIDE";
pptx.author = "NovaSteel";
pptx.company = "NovaSteel";
pptx.subject = "NovaSteel oral defense";
pptx.title = "NovaSteel — AI-Powered Steel Production Optimization Platform";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: F.head,
  bodyFontFace: F.body,
  lang: "en-US",
};

const S = pptx.ShapeType;
const texture = path.join(ASSETS, "steel-texture.png");
const hero = path.join(ASSETS, "steelworks-hero.png");
const thermalMap = path.join(ASSETS, "thermal-map.png");

function ensureAsset(file) {
  if (!fs.existsSync(file)) {
    throw new Error(`Missing visual asset: ${file}. Run npm run assets first.`);
  }
}

function tx(slide, value, x, y, w, h, options = {}) {
  slide.addText(value, {
    x, y, w, h,
    margin: 0,
    fontFace: options.fontFace || F.body,
    fontSize: options.fontSize || 13,
    color: options.color || C.ink,
    bold: options.bold || false,
    italic: options.italic || false,
    breakLine: options.breakLine,
    align: options.align || "left",
    valign: options.valign || "mid",
    fit: options.fit || "shrink",
    paraSpaceAfterPt: options.paraSpaceAfterPt || 0,
    charSpacing: options.charSpacing,
    transparency: options.transparency,
  });
}

function rect(slide, x, y, w, h, fill, line = fill, opts = {}) {
  slide.addShape(opts.type || S.rect, {
    x, y, w, h,
    fill: { color: fill, transparency: opts.transparency || 0 },
    line: { color: line, transparency: opts.lineTransparency || 0, width: opts.lineWidth || 0.5 },
    radius: opts.radius,
  });
}

function roundRect(slide, x, y, w, h, fill, line = fill, opts = {}) {
  rect(slide, x, y, w, h, fill, line, { ...opts, type: S.roundRect });
}

function circle(slide, x, y, d, fill, line = fill, opts = {}) {
  slide.addShape(S.ellipse, {
    x, y, w: d, h: d,
    fill: { color: fill, transparency: opts.transparency || 0 },
    line: { color: line, transparency: opts.lineTransparency || 0, width: opts.lineWidth || 0.5 },
  });
}

function line(slide, x, y, w, h, color, width = 1, dash = "solid") {
  const x0 = w < 0 ? x + w : x;
  const y0 = h < 0 ? y + h : y;
  slide.addShape(S.line, {
    x: x0, y: y0, w: Math.abs(w), h: Math.abs(h),
    flipH: (w < 0) !== (h < 0),
    line: { color, width, dash },
  });
}

function chevron(slide, x, y, w, h, color) {
  slide.addShape(S.chevron, {
    x, y, w, h,
    fill: { color },
    line: { color, transparency: 100 },
  });
}

function badge(slide, x, y, label, kind = "context", minWidth = 0) {
  const styles = {
    target: { fill: C.amber, text: C.carbon, line: C.amber },
    evidence: { fill: C.teal, text: C.white, line: C.teal },
    context: { fill: C.graphite, text: C.white, line: C.graphite },
    guardrail: { fill: C.rust, text: C.white, line: C.rust },
    backup: { fill: C.oxide, text: C.white, line: C.oxide },
  };
  const style = styles[kind];
  const width = Math.max(0.9, minWidth, label.length * 0.066 + 0.32);
  roundRect(slide, x, y, width, 0.27, style.fill, style.line, { lineWidth: 0.4 });
  tx(slide, label.toUpperCase(), x + 0.13, y + 0.055, width - 0.26, 0.13, {
    fontSize: 7.2, color: style.text, bold: true, charSpacing: 1.1,
  });
  return width;
}

function label(slide, x, y, text, color = C.muted, width = 2) {
  tx(slide, text.toUpperCase(), x, y, width, 0.16, {
    fontSize: 7.2, color, bold: true, charSpacing: 1.2,
  });
}

function addCanvas(slide, dark = false, withTexture = false) {
  slide.background = { color: dark ? C.carbon : C.paper };
  if (dark && withTexture) {
    slide.addImage({ path: texture, x: 0, y: 0, w: W, h: H, transparency: 66 });
  }
  if (!dark) {
    circle(slide, 11.15, 0.08, 1.82, C.paleAmber, C.paleAmber, { transparency: 25 });
    circle(slide, 0.08, 5.45, 1.58, C.paleTeal, C.paleTeal, { transparency: 35 });
  }
}

function addHeader(slide, index, kicker, title, timing, dark = false, backup = false) {
  const main = dark ? C.white : C.ink;
  const soft = dark ? C.steel : C.muted;
  badge(slide, 0.5, 0.3, backup ? `Backup ${index - 20}` : `Slide ${String(index).padStart(2, "0")}`, backup ? "backup" : "context");
  tx(slide, kicker.toUpperCase(), 1.65, 0.34, 6.9, 0.18, {
    fontSize: 8.1, color: soft, bold: true, charSpacing: 1.3,
  });
  if (timing) {
    roundRect(slide, 10.98, 0.3, 1.83, 0.28, dark ? C.coal : C.white, dark ? C.graphite : C.mist, { lineWidth: 0.5 });
    tx(slide, timing, 11.13, 0.37, 1.54, 0.11, {
      fontSize: 7.2, color: soft, bold: true, align: "center",
    });
  }
  tx(slide, title, 0.5, 0.69, 12.15, 0.47, {
    fontFace: F.head, fontSize: 25.5, color: main, bold: true,
  });
}

function addFooter(slide, index, dark = false) {
  const footerFill = dark ? C.coal : "E9E7E1";
  const footerText = dark ? C.mist : C.graphite;
  rect(slide, 0, 7.09, W, 0.41, footerFill, footerFill);
  roundRect(slide, 0.42, 7.16, 3.88, 0.2, dark ? C.graphite : C.white, dark ? C.graphite : C.mist, { lineWidth: 0.25 });
  tx(slide, "SYNTHETIC DEMONSTRATION  |  NOT FOR OPERATIONAL CONTROL", 0.56, 7.205, 3.6, 0.08, {
    fontSize: 6.25, color: footerText, bold: true, charSpacing: 0.65,
  });
  tx(slide, index <= 20 ? `ORAL DEFENSE  •  ${String(index).padStart(2, "0")} / 20` : `FAQ & VALIDATION BACKUP  •  ${String(index - 20).padStart(2, "0")} / ${String(BACKUP_SLIDES).padStart(2, "0")}`, 9.55, 7.205, 3.3, 0.08, {
    fontSize: 6.5, color: footerText, bold: true, align: "right", charSpacing: 0.5,
  });
}

function finish(slide, index, notes, source, dark = false) {
  if (source) {
    tx(slide, source, 0.5, 6.8, 12.2, 0.14, {
      fontSize: 6.6, color: dark ? C.steel : C.muted, italic: true,
    });
  }
  addFooter(slide, index, dark);
  if (typeof slide.addNotes === "function") {
    slide.addNotes(notes.split("\n").filter(Boolean));
  }
}

function newSlide(index, kicker, title, timing, opts = {}) {
  const slide = pptx.addSlide();
  addCanvas(slide, opts.dark || false, opts.texture || false);
  addHeader(slide, index, kicker, title, timing, opts.dark || false, opts.backup || false);
  return slide;
}

function card(slide, x, y, w, h, opts = {}) {
  const dark = opts.dark || false;
  const fill = opts.fill || (dark ? C.coal : C.white);
  const border = opts.border || (dark ? C.graphite : C.mist);
  roundRect(slide, x, y, w, h, fill, border, { lineWidth: opts.lineWidth || 0.7 });
  if (opts.bar) {
    rect(slide, x, y, 0.085, h, opts.bar, opts.bar, { lineWidth: 0 });
  }
}

function metricCard(slide, x, y, w, h, value, caption, type, detail, opts = {}) {
  const dark = opts.dark || false;
  const valueColor = type === "target" ? C.rust : type === "evidence" ? C.teal : (dark ? C.white : C.ink);
  card(slide, x, y, w, h, { dark, fill: opts.fill, border: opts.border, bar: valueColor });
  badge(slide, x + 0.22, y + 0.2, type, type);
  tx(slide, value, x + 0.22, y + 0.63, w - 0.4, 0.48, {
    fontFace: F.head, fontSize: opts.valueSize || 25, color: valueColor, bold: true,
  });
  tx(slide, caption, x + 0.22, y + 1.16, w - 0.4, 0.31, {
    fontSize: 10.6, color: dark ? C.white : C.ink, bold: true,
  });
  tx(slide, detail, x + 0.22, y + h - 0.37, w - 0.4, 0.18, {
    fontSize: 7.6, color: dark ? C.steel : C.muted,
  });
}

function stage(slide, x, y, w, h, title, detail, color, opts = {}) {
  card(slide, x, y, w, h, {
    dark: opts.dark || false,
    fill: opts.fill || (opts.dark ? C.coal : C.white),
    border: opts.border || color,
    bar: color,
    lineWidth: 0.7,
  });
  tx(slide, title, x + 0.18, y + 0.2, w - 0.35, 0.24, {
    fontSize: opts.titleSize || 10.2, color: opts.dark ? C.white : C.ink, bold: true,
  });
  tx(slide, detail, x + 0.18, y + 0.53, w - 0.35, h - 0.65, {
    fontSize: opts.detailSize || 8, color: opts.dark ? C.steel : C.muted, valign: "top",
  });
}

function personTile(slide, x, y, w, h, initials, role, cockpit, tone) {
  card(slide, x, y, w, h, { fill: C.white, border: C.mist, bar: tone });
  circle(slide, x + 0.18, y + 0.2, 0.47, tone, tone);
  tx(slide, initials, x + 0.18, y + 0.315, 0.47, 0.1, { fontSize: 8, color: C.white, bold: true, align: "center" });
  tx(slide, role, x + 0.78, y + 0.18, w - 0.92, 0.18, { fontSize: 8.6, color: C.ink, bold: true });
  tx(slide, cockpit, x + 0.78, y + 0.45, w - 0.92, 0.22, { fontSize: 7.4, color: C.muted });
}

function fact(slide, x, y, number, title, detail, tone, opts = {}) {
  circle(slide, x, y, 0.42, tone, tone);
  tx(slide, number, x, y + 0.115, 0.42, 0.1, { fontSize: 7.3, color: C.white, bold: true, align: "center" });
  tx(slide, title, x + 0.58, y - 0.005, opts.w || 2.2, 0.17, { fontSize: 9.2, color: opts.dark ? C.white : C.ink, bold: true });
  tx(slide, detail, x + 0.58, y + 0.25, opts.w || 2.2, 0.28, { fontSize: 7.8, color: opts.dark ? C.steel : C.muted, valign: "top" });
}

function sourceBar(slide, x, y, w, labels) {
  labels.forEach((entry, i) => {
    const cell = w / labels.length;
    const color = entry.color || C.graphite;
    roundRect(slide, x + i * cell, y, cell - 0.08, 0.34, C.white, C.mist, { lineWidth: 0.4 });
    rect(slide, x + i * cell, y, 0.06, 0.34, color, color);
    tx(slide, entry.text, x + i * cell + 0.13, y + 0.105, cell - 0.22, 0.1, { fontSize: 7.4, color: C.ink, bold: true, align: "center" });
  });
}

function addSmallFactory(slide, x, y, scale = 1, dark = false) {
  const metal = dark ? C.steel : C.graphite;
  const glow = C.rust;
  rect(slide, x, y + 1.05 * scale, 3.25 * scale, 0.1 * scale, metal, metal);
  rect(slide, x + 0.15 * scale, y + 0.55 * scale, 0.33 * scale, 0.5 * scale, metal, metal);
  rect(slide, x + 0.78 * scale, y + 0.27 * scale, 0.36 * scale, 0.78 * scale, metal, metal);
  rect(slide, x + 1.62 * scale, y + 0.44 * scale, 0.48 * scale, 0.61 * scale, metal, metal);
  rect(slide, x + 2.61 * scale, y + 0.12 * scale, 0.42 * scale, 0.93 * scale, metal, metal);
  rect(slide, x + 0.75 * scale, y + 0.35 * scale, 0.42 * scale, 0.04 * scale, glow, glow);
  rect(slide, x + 2.58 * scale, y + 0.26 * scale, 0.48 * scale, 0.04 * scale, glow, glow);
  [0.15, 0.55, 1.2, 1.78, 2.38, 3.0].forEach((pos) => line(slide, x + pos * scale, y + 1.05 * scale, 0.33 * scale, -0.5 * scale, metal, 0.8));
}

function addThermalLegend(slide, x, y) {
  ["Base", "Watch", "Warm"].forEach((name, i) => {
    const color = [C.teal, C.amber, C.rust][i];
    circle(slide, x + i * 0.85, y, 0.14, color, color);
    tx(slide, name, x + i * 0.85 + 0.2, y + 0.015, 0.53, 0.08, { fontSize: 6.4, color: C.muted });
  });
}

// 01 — framing
{
  const slide = newSlide(1, "Opening position", "NovaSteel | AI-powered steel production optimization", "00:00–00:45", { dark: true, texture: true });
  slide.addImage({ path: hero, x: 0, y: 0, w: W, h: H });
  rect(slide, 0, 0, W, H, C.carbon, C.carbon, { transparency: 19 });
  rect(slide, 0, 0, 5.65, H, C.carbon, C.carbon, { transparency: 9 });
  tx(slide, "NOVA STEEL", 0.58, 1.03, 3.1, 0.2, {
    fontFace: F.head, fontSize: 12.5, color: C.amber, bold: true, charSpacing: 2.4,
  });
  badge(slide, 0.58, 1.35, "Oral defense", "context");
  tx(slide, "ONE GOVERNED DATA CORE\nFOR A FOUR-COUNTRY STEEL ESTATE", 0.58, 1.85, 6.45, 1.35, {
    fontFace: F.head, fontSize: 30.5, color: C.white, bold: true, valign: "top",
  });
  tx(slide, "35 min architecture & value  |  10 min deterministic demo  |  15 min hard questions", 0.58, 3.36, 6.45, 0.25, {
    fontSize: 12.5, color: C.mist, bold: true,
  });
  roundRect(slide, 0.58, 3.94, 5.18, 1.02, C.coal, C.graphite, { lineWidth: 0.7 });
  tx(slide, "HONESTY CONTRACT", 0.83, 4.18, 1.86, 0.15, { fontSize: 8, color: C.amber, bold: true, charSpacing: 1.1 });
  tx(slide, "Targets are ambition. The live demo is reproducible synthetic evidence of mechanics — not realized production savings.", 0.83, 4.43, 4.52, 0.31, {
    fontSize: 11.2, color: C.white, bold: true, valign: "top",
  });
  addSmallFactory(slide, 8.68, 5.64, 1.16, true);
  tx(slide, "MICROSOFT FABRIC–CENTERED  |  SYNTHETIC DEMONSTRATION", 0.58, 5.98, 5.2, 0.17, { fontSize: 8.7, color: C.steel, bold: true, charSpacing: 1.15 });
  finish(
    slide,
    1,
    "Good morning. In the next hour I will defend NovaSteel: 35 minutes of architecture and value, a 10-minute live demonstration on fully synthetic data, and 15 minutes for hard questions.\nThe ground rule is visible from the first slide: I will distinguish a business target from evidence we can reproduce. The demo proves mechanics on synthetic data; it does not claim banked savings.",
    "Source cue | solution-architecture.md §1.1  •  demo-runbook.md §1",
    true,
  );
}

// 02 — business challenge
{
  const slide = newSlide(2, "The business case", "A steel estate under pressure on five fronts", "00:45–02:25");
  badge(slide, 0.5, 1.31, "Context", "context");
  roundRect(slide, 0.5, 1.7, 4.15, 4.56, C.coal, C.coal);
  tx(slide, "FOUR-COUNTRY\nSTEEL ESTATE", 0.78, 1.98, 2.3, 0.4, { fontFace: F.head, fontSize: 20, color: C.white, bold: true });
  tx(slide, "Luxembourg hub\nGermany • Belgium • Spain", 0.78, 2.62, 2.4, 0.34, { fontSize: 10, color: C.steel });
  const sites = [
    { x: 1.2, y: 3.65, label: "LU", plant: "Moselle", c: C.rust },
    { x: 3.2, y: 3.15, label: "DE", plant: "Rhine", c: C.amber },
    { x: 0.9, y: 4.95, label: "BE", plant: "Meuse", c: C.teal },
    { x: 3.34, y: 5.1, label: "ES", plant: "Ebro", c: C.green },
  ];
  line(slide, 2.36, 4.38, 0.85, -0.8, C.graphite, 2);
  line(slide, 2.36, 4.38, -1.2, 0.73, C.graphite, 2);
  line(slide, 2.36, 4.38, 1.15, 0.75, C.graphite, 2);
  sites.forEach((s) => {
    circle(slide, s.x, s.y, 0.72, s.c, s.c);
    tx(slide, s.label, s.x, s.y + 0.21, 0.72, 0.12, { fontSize: 10, color: C.white, bold: true, align: "center" });
    tx(slide, s.plant, s.x - 0.18, s.y + 0.83, 1.1, 0.12, { fontSize: 6.9, color: C.steel, bold: true, align: "center" });
  });
  circle(slide, 2.13, 4.14, 0.48, C.white, C.white);
  tx(slide, "HQ", 2.13, 4.31, 0.48, 0.08, { fontSize: 6.8, color: C.coal, bold: true, align: "center" });
  const pains = [
    ["35%", "Energy of modeled production cost", C.rust],
    ["CO₂", "EU ETS financial exposure", C.amber],
    ["€8M", "Unpredicted lining-failure scale", C.red],
    ["QA", "Automotive-grade yield variability", C.teal],
    ["KN", "Retiring expertise leaves with people", C.green],
  ];
  pains.forEach((p, i) => {
    const y = 1.62 + i * 0.88;
    circle(slide, 5.28, y + 0.02, 0.54, p[2], p[2]);
    tx(slide, p[0], 5.28, y + 0.20, 0.54, 0.09, { fontSize: 7.1, color: C.white, bold: true, align: "center" });
    tx(slide, p[1], 6.02, y + 0.04, 4.45, 0.18, { fontSize: 12.5, color: C.ink, bold: true });
    tx(slide, i === 0 ? "No real-time optimization lever today" : i === 1 ? "Carbon is a hard business cost" : i === 2 ? "Risk today is reactive, not planned" : i === 3 ? "Genealogy must be heat-by-heat" : "Tacit checks must be captured safely", 6.02, y + 0.33, 5.35, 0.14, { fontSize: 8.5, color: C.muted });
  });
  finish(slide, 2,
    "NovaSteel operates blast-furnace and rolling processes across four EU countries. The pain is not a generic digital problem: energy is material, carbon carries financial exposure, a lining failure can be an eight-million-euro event, automotive yield must be traceable, and retiring operators take hard-won know-how with them.\nThis is heavy industry, safety-sensitive, and EU-regulated; every later design choice answers one of these pressures.",
    "Source cue | usecase.md  •  personas-and-journeys.md",
  );
}

// 03 — cost of standing still
{
  const slide = newSlide(3, "Executive urgency", "Doing nothing is not a neutral option", "02:25–03:50", { dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Illustrative exposure", "context");
  tx(slide, "REACTIVE OPERATIONS\nPAY THE MAXIMUM ON EVERY AXIS.", 0.52, 1.74, 5.1, 0.68, {
    fontFace: F.head, fontSize: 23.5, color: C.white, bold: true, valign: "top",
  });
  tx(slide, "No invented aggregate ROI. The exposure categories are deliberately visible, not rolled into a fake total.", 0.52, 2.73, 4.65, 0.29, {
    fontSize: 10, color: C.steel, valign: "top",
  });
  const exposures = [
    { label: "Peak energy", val: 5.2, c: C.rust, note: "buying at the wrong time" },
    { label: "ETS exposure", val: 4.1, c: C.amber, note: "carbon becomes material" },
    { label: "Unplanned reline", val: 6.4, c: C.red, note: "≈ €8M + outage" },
    { label: "Yield / claims", val: 3.5, c: C.teal, note: "late drift is costly" },
    { label: "Knowledge attrition", val: 4.8, c: C.green, note: "irreversible loss" },
  ];
  exposures.forEach((e, i) => {
    const y = 1.58 + i * 0.86;
    tx(slide, e.label, 6.1, y, 1.75, 0.16, { fontSize: 9.5, color: C.white, bold: true, align: "right" });
    roundRect(slide, 8.1, y, 3.72, 0.32, C.graphite, C.graphite);
    roundRect(slide, 8.1, y, e.val * 0.53, 0.32, e.c, e.c);
    tx(slide, e.note, 8.18, y + 0.42, 3.58, 0.12, { fontSize: 7.3, color: C.steel, align: "right" });
  });
  circle(slide, 1.0, 4.25, 1.35, C.coal, C.rust, { lineWidth: 2 });
  tx(slide, "WAIT", 1.0, 4.75, 1.35, 0.2, { fontFace: F.head, fontSize: 13, color: C.amber, bold: true, align: "center" });
  line(slide, 2.45, 4.92, 2.05, 0, C.rust, 2.5);
  chevron(slide, 4.28, 4.72, 0.34, 0.4, C.rust);
  tx(slide, "Every delay compounds exposure.", 0.88, 5.95, 4.25, 0.18, { fontSize: 10.5, color: C.white, bold: true });
  finish(slide, 3,
    "Doing nothing is the expensive decision. It keeps buying energy at peaks, paying carbon exposure, accepting reactive lining risk, finding quality drift too late, and losing experts permanently.\nI am deliberately not presenting an invented total-savings number. The point is materiality and direction; the pilot creates a defensible measured value case.",
    "Source cue | usecase.md  •  personas-and-journeys.md",
    true,
  );
}

// 04 — transformation targets
{
  const slide = newSlide(4, "Transformation objective", "Four falsifiable targets — not demo claims", "03:50–05:30");
  badge(slide, 0.5, 1.3, "Targets", "target");
  tx(slide, "Every headline target carries a baseline. The demonstration shows mechanics, not realized production outcomes.", 2.04, 1.36, 8.1, 0.15, { fontSize: 9.6, color: C.muted, bold: true });
  const cards = [
    ["−14%", "Energy / ton", "~19.5 → ~16.8 GJ/t", "KPI-ENE-01"],
    ["−22%", "CO₂ / ton", "~2.10 → ~1.64 t/t", "KPI-CO2-01"],
    ["≥21 d", "Lining warning", "advance-warning target", "KPI-FUR-01"],
    ["+8%", "High-grade yield", "~90% → ~97%", "KPI-QUA-01"],
  ];
  cards.forEach((m, i) => {
    const x = 0.5 + i * 3.15;
    metricCard(slide, x, 2.05, 2.82, 2.7, m[0], m[1], "target", `${m[2]}  |  ${m[3]}`, { valueSize: i === 2 ? 22 : 27 });
    circle(slide, x + 1.96, 3.67, 0.45, C.paleAmber, C.amber, { lineWidth: 1 });
    tx(slide, "T", x + 1.96, 3.83, 0.45, 0.08, { fontSize: 7, color: C.rust, bold: true, align: "center" });
  });
  roundRect(slide, 0.5, 5.25, 12.05, 1.05, C.white, C.mist, { lineWidth: 0.8 });
  circle(slide, 0.8, 5.55, 0.42, C.teal, C.teal);
  tx(slide, "E", 0.8, 5.69, 0.42, 0.08, { fontSize: 7.5, color: C.white, bold: true, align: "center" });
  tx(slide, "DEMONSTRATION EVIDENCE", 1.42, 5.43, 2.7, 0.14, { fontSize: 8, color: C.teal, bold: true, charSpacing: 1.0 });
  tx(slide, "A deterministic synthetic run can produce RUL bands, a feasible dispatch, quality what-ifs, and auditable human decisions. It cannot bank the four targets.", 1.42, 5.72, 10.45, 0.18, { fontSize: 10.4, color: C.ink, bold: true });
  finish(slide, 4,
    "These four figures are transformation targets, not victory laps. Each is tied to a stated baseline, which makes it falsifiable. We will prove or disprove them through a one-site pilot and an auditable savings ledger.\nThe demo later shows deterministic synthetic evidence: model bands, feasible schedules, what-ifs, lineage, and approvals. It does not convert the targets into realized production results.",
    "Source cue | solution-requirements.md §4, §13  •  usecase.md",
  );
}

// 05 — one governed platform
{
  const slide = newSlide(5, "Solution overview", "One governed platform: signals → intelligence → accountable decisions", "05:30–07:10", { dark: true, texture: true });
  const nodes = [
    { x: 0.75, y: 2.18, d: 1.35, title: "PLANT\nSIGNALS", sub: "OT / MES / market", color: C.rust },
    { x: 3.25, y: 2.18, d: 1.6, title: "FABRIC\nCORE", sub: "governed data spine", color: C.teal },
    { x: 6.25, y: 2.18, d: 1.35, title: "FOUR AI\nCAPABILITIES", sub: "Python + constrained GenAI", color: C.amber },
    { x: 8.75, y: 2.18, d: 1.35, title: "PERSONA\nEXPERIENCE", sub: "8 role-specific views", color: C.green },
    { x: 11.22, y: 2.18, d: 1.35, title: "HUMAN\nDECISION", sub: "approval + audit", color: C.rust },
  ];
  nodes.forEach((n, i) => {
    circle(slide, n.x, n.y, n.d, C.coal, n.color, { lineWidth: 2.1 });
    tx(slide, n.title, n.x + 0.1, n.y + 0.34, n.d - 0.2, 0.31, { fontFace: F.head, fontSize: 10.3, color: C.white, bold: true, align: "center", valign: "mid" });
    tx(slide, n.sub, n.x - 0.2, n.y + n.d + 0.18, n.d + 0.4, 0.17, { fontSize: 7.4, color: C.steel, align: "center" });
    if (i < nodes.length - 1) chevron(slide, n.x + n.d + 0.3, 2.72, 0.47, 0.34, C.graphite);
  });
  circle(slide, 4.37, 2.82, 0.44, C.teal, C.teal);
  tx(slide, "1", 4.37, 2.98, 0.44, 0.07, { fontSize: 7, color: C.white, bold: true, align: "center" });
  roundRect(slide, 0.75, 5.1, 11.82, 0.88, C.coal, C.graphite, { lineWidth: 0.7 });
  tx(slide, "The operating contract", 1.02, 5.33, 2.0, 0.13, { fontSize: 8, color: C.amber, bold: true, charSpacing: 0.9 });
  tx(slide, "Fabric unifies production, energy, emissions, quality, maintenance, and knowledge. Every consequential output stays advisory, human-approved, and append-only auditable.", 3.1, 5.25, 8.9, 0.22, { fontSize: 11.2, color: C.white, bold: true, align: "center" });
  finish(slide, 5,
    "This is the whole answer in one picture. Signals flow through a Fabric data core, four capabilities make them useful, persona views make them actionable, and humans take accountable decisions.\nFabric is deliberately the center of gravity. It prevents a collection of disconnected dashboards, models, and data copies. The platform never actuates equipment.",
    "Source cue | solution-architecture.md §3",
    true,
  );
}

// 06 — guardrails
{
  const slide = newSlide(6, "Safety and trust", "Five guardrails we will not trade away", "07:10–08:55");
  badge(slide, 0.5, 1.3, "Non-negotiable", "guardrail");
  const locks = [
    ["01", "Decision support\nnot control", "No PLC, interlock, furnace, or setpoint write", C.rust],
    ["02", "Synthetic-only\ndemonstration", "Isolated demo data, identities, capacity", C.amber],
    ["03", "EU-only\nposture", "Sweden Central primary; Data Zone (EU)", C.teal],
    ["04", "Append-only\naudit", "Inputs, version, confidence, decision, outcome", C.green],
    ["05", "No standing\nsecrets", "Entra managed identities by workload", C.graphite],
  ];
  locks.forEach((l, i) => {
    const x = 0.5 + i * 2.48;
    card(slide, x, 2.03, 2.18, 3.5, { fill: C.white, border: C.mist, bar: l[3] });
    circle(slide, x + 0.68, 2.46, 0.83, l[3], l[3]);
    tx(slide, l[0], x + 0.68, 2.75, 0.83, 0.12, { fontFace: F.head, fontSize: 13, color: C.white, bold: true, align: "center" });
    line(slide, x + 0.93, 2.52, 0, -0.18, l[3], 1.5);
    line(slide, x + 1.27, 2.52, 0, -0.18, l[3], 1.5);
    line(slide, x + 0.93, 2.34, 0.34, 0, l[3], 1.5);
    tx(slide, l[1], x + 0.21, 3.55, 1.75, 0.45, { fontFace: F.head, fontSize: 11, color: C.ink, bold: true, align: "center" });
    tx(slide, l[2], x + 0.22, 4.47, 1.72, 0.4, { fontSize: 8.2, color: C.muted, align: "center", valign: "top" });
  });
  roundRect(slide, 0.5, 6.05, 12.05, 0.46, C.coal, C.coal);
  tx(slide, "If a proposed feature weakens any one of these, it is outside the demonstration contract.", 0.75, 6.2, 11.55, 0.12, { fontSize: 10, color: C.white, bold: true, align: "center" });
  finish(slide, 6,
    "Five guardrails constrain the solution. First and most important, this is decision support; nothing writes to a control system. The demonstration is synthetic and isolated. Processing is EU-only. Every consequential output is auditable. And there are no standing application secrets.\nThese are not ambitions. They are acceptance boundaries.",
    "Source cue | solution-architecture.md §1.1, ADR-007/008  •  security-governance-and-threat-model.md",
  );
}

// 07 — personas
{
  const slide = newSlide(7, "Value by role", "Eight personas, one operating story", "08:55–10:35");
  badge(slide, 0.5, 1.3, "Persona journeys", "context");
  const people = [
    ["PM", "Plant Manager", "Site Command Center", C.rust],
    ["EX", "Executive", "Value & ROI Cockpit", C.graphite],
    ["RE", "Reliability Engineer", "Furnace RUL", C.amber],
    ["OP", "Furnace Operator", "Health + Knowledge", C.green],
    ["EN", "Energy Manager", "Dispatch Optimization", C.teal],
    ["SU", "Sustainability", "ETS Cockpit", C.rust],
    ["QA", "Quality Engineer", "In-line Quality", C.amber],
    ["KE", "Knowledge Engineer", "Capture Studio", C.teal],
  ];
  people.forEach((p, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    personTile(slide, 0.5 + col * 3.02, 2.0 + row * 1.34, 2.72, 0.96, p[0], p[1], p[2], p[3]);
  });
  const flowY = 5.42;
  const stages = [
    ["See", "fleet / freshness", C.graphite],
    ["Investigate", "risk / lineage", C.teal],
    ["Simulate", "bounded what-if", C.amber],
    ["Approve", "human decision", C.rust],
    ["Learn", "audit outcome", C.green],
  ];
  stages.forEach((s, i) => {
    const x = 0.63 + i * 2.45;
    circle(slide, x, flowY, 0.42, s[2], s[2]);
    tx(slide, String(i + 1), x, flowY + 0.135, 0.42, 0.08, { fontSize: 7, color: C.white, bold: true, align: "center" });
    tx(slide, s[0], x + 0.55, flowY + 0.02, 1.03, 0.12, { fontSize: 8.4, color: C.ink, bold: true });
    tx(slide, s[1], x + 0.55, flowY + 0.21, 1.3, 0.09, { fontSize: 6.9, color: C.muted });
    if (i < stages.length - 1) chevron(slide, x + 1.92, flowY + 0.1, 0.26, 0.22, C.graphite);
  });
  finish(slide, 7,
    "The platform serves eight roles, not one generic dashboard. Plant leaders see a defendable operating picture; reliability sees an evidence-backed lining risk; energy sees feasible dispatch; quality sees genealogy; knowledge owners see reviewed drafts.\nThe demo follows these experiences in the order an operating day touches them.",
    "Source cue | personas-and-journeys.md  •  demo-runbook.md §2",
  );
}

// 08 — architecture
{
  const slide = newSlide(8, "Architecture map", "From plant signal to governed persona experience", "10:35–12:55", { dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Sweden Central + EU", "context");
  const cols = [
    { x: 0.52, w: 2.1, title: "SITES", detail: "Purdue L3.5\nOT gateway\noutbound only", c: C.rust },
    { x: 2.91, w: 2.1, title: "INGRESS", detail: "Event Hubs\nMI relay\nno SAS", c: C.amber },
    { x: 5.3, w: 2.7, title: "FABRIC CORE", detail: "Eventstream → KQL\nOneLake → Delta\nDirect Lake", c: C.teal },
    { x: 8.29, w: 2.1, title: "AI + API", detail: "Python workers\nFoundry + Speech\nFastAPI BFF", c: C.green },
    { x: 10.68, w: 2.1, title: "EXPERIENCE", detail: "Blazor shell\nReact / MUI / D3\nPower BI internal", c: C.rust },
  ];
  cols.forEach((c, i) => {
    roundRect(slide, c.x, 2.02, c.w, 2.75, C.coal, c.c, { lineWidth: 1.25 });
    rect(slide, c.x, 2.02, c.w, 0.1, c.c, c.c);
    tx(slide, c.title, c.x + 0.2, 2.37, c.w - 0.4, 0.18, { fontFace: F.head, fontSize: 11, color: C.white, bold: true, align: "center" });
    tx(slide, c.detail, c.x + 0.18, 2.91, c.w - 0.36, 0.63, { fontSize: 9, color: C.steel, align: "center", valign: "mid" });
    if (i < cols.length - 1) chevron(slide, c.x + c.w + 0.08, 3.1, 0.19, 0.35, C.graphite);
  });
  tx(slide, "FABRIC IS THE DATA AND ANALYTICS SPINE", 5.45, 4.09, 2.4, 0.21, { fontSize: 8.4, color: C.teal, bold: true, align: "center", charSpacing: 0.7 });
  const controls = [
    ["Outbound OT", "No cloud session into plant", C.rust],
    ["Entra identity", "No SAS / standing app secrets", C.amber],
    ["Dual stores", "Hot KQL + governed Delta", C.teal],
    ["Human decision", "No autonomous actuation", C.green],
  ];
  controls.forEach((c, i) => {
    const x = 0.72 + i * 3.05;
    fact(slide, x, 5.42, String(i + 1), c[0], c[1], c[2], { dark: true, w: 2.15 });
  });
  finish(slide, 8,
    "Read this architecture left to right. A per-site gateway in an industrial DMZ emits outbound, validated telemetry. Event Hubs buffers it; a managed-identity relay publishes to Fabric Eventstream without a shared key.\nFabric is the core: KQL for hot operations, OneLake Delta for governed history, and Direct Lake for one semantic truth. Python performs authoritative calculations; Foundry and Speech handle constrained language workflows; the browser is a Blazor shell hosting React analytics.",
    "Source cue | solution-architecture.md §3  •  deployment-topology.md §3",
    true,
  );
}

// 09 — Fabric centrality
{
  const slide = newSlide(9, "Architecture decision ADR-001/002", "Why Fabric is the center of gravity", "12:55–15:10");
  badge(slide, 0.5, 1.3, "Fabric spine", "context");
  circle(slide, 4.75, 2.18, 3.12, C.coal, C.teal, { lineWidth: 2.4 });
  circle(slide, 5.52, 2.95, 1.58, C.teal, C.teal);
  tx(slide, "MICROSOFT\nFABRIC", 5.62, 3.4, 1.38, 0.26, { fontFace: F.head, fontSize: 12, color: C.white, bold: true, align: "center" });
  const fabricNodes = [
    ["RTI", "Eventstream +\nEventhouse/KQL", 3.43, 2.06, C.rust],
    ["ONE", "OneLake +\nLakehouse", 7.18, 2.06, C.teal],
    ["DL", "Direct Lake\none semantic truth", 3.53, 4.86, C.amber],
    ["BI", "Power BI +\nnotify-only Activator", 7.1, 4.86, C.green],
  ];
  fabricNodes.forEach((n) => {
    circle(slide, n[2], n[3], 1.23, C.white, n[4], { lineWidth: 1.3 });
    tx(slide, n[0], n[2], n[3] + 0.27, 1.23, 0.15, { fontFace: F.head, fontSize: 12, color: n[4], bold: true, align: "center" });
    tx(slide, n[1], n[2] - 0.3, n[3] + 1.32, 1.83, 0.25, { fontSize: 7.5, color: C.muted, bold: true, align: "center" });
  });
  roundRect(slide, 9.55, 1.88, 2.58, 3.68, C.white, C.mist, { lineWidth: 0.8 });
  label(slide, 9.84, 2.18, "One core, many clocks", C.teal, 1.9);
  fact(slide, 9.84, 2.68, "1", "Hot operations", "freshness, alarms, high-cardinality telemetry", C.rust, { w: 1.7 });
  fact(slide, 9.84, 3.62, "2", "Governed history", "bronze → silver → gold Delta", C.teal, { w: 1.7 });
  fact(slide, 9.84, 4.56, "3", "One KPI meaning", "no parallel lake or BI store", C.amber, { w: 1.7 });
  roundRect(slide, 0.54, 5.95, 8.3, 0.53, C.paleTeal, C.teal, { lineWidth: 0.7 });
  tx(slide, "ADR-001: no parallel data lake or BI store.  ADR-002: hot KQL is separate from governed Delta.", 0.77, 6.145, 7.8, 0.1, { fontSize: 8.8, color: C.ink, bold: true, align: "center" });
  finish(slide, 9,
    "Heavy-industry analytics has two clocks: a hot operational clock and a governed history clock. Fabric gives both a single governed estate. Eventstream and Eventhouse KQL support fresh operations; OneLake Delta preserves history and model inputs; Direct Lake keeps one KPI definition.\nADR-001 rejects a parallel lake and BI stack. ADR-002 separates hot KQL from Delta, so the same store is not forced to answer incompatible questions.",
    "Source cue | solution-architecture.md §3.1, ADR-001, ADR-002  •  fabric-platform.md",
  );
}

// 10 — trusted data
{
  const slide = newSlide(10, "Trustworthy data", "The path from OT signal to governed fact", "15:10–17:10");
  badge(slide, 0.5, 1.3, "Architecture fact", "context");
  const pipeline = [
    ["DMZ\nGATEWAY", "schema + allow list", C.rust],
    ["EVENT\nHUBS", "buffer + replay", C.amber],
    ["MI\nRELAY", "Entra, no SAS", C.graphite],
    ["EVENT\nSTREAM", "light route / shape", C.teal],
    ["BRONZE", "immutable envelope", C.teal],
    ["SILVER", "dedup + normalize", C.green],
    ["GOLD", "facts + audit", C.rust],
  ];
  pipeline.forEach((p, i) => {
    const x = 0.48 + i * 1.78;
    stage(slide, x, 2.07, 1.48, 1.18, p[0], p[1], p[2], { titleSize: 9.2, detailSize: 6.85 });
    if (i < pipeline.length - 1) chevron(slide, x + 1.52, 2.48, 0.18, 0.28, C.graphite);
  });
  roundRect(slide, 8.64, 3.82, 3.78, 1.05, C.paleRust, C.rust, { lineWidth: 0.9 });
  badge(slide, 8.94, 4.08, "Visible quarantine", "guardrail");
  tx(slide, "Late • duplicate • invalid unit • unknown asset\nare retained with a reason — never silently repaired.", 8.94, 4.48, 3.05, 0.25, { fontSize: 9.2, color: C.ink, bold: true, align: "center", valign: "mid" });
  line(slide, 6.76, 3.2, 2.03, 0.85, C.rust, 1.8, "dash");
  const facts = [
    ["Envelope", "UUIDv7, event time, sequence, source, schema, class", C.graphite],
    ["One contract", "Streaming + batch converge in silver", C.teal],
    ["Ingress isolation", "Publisher has a narrow RTI workspace blast radius", C.amber],
  ];
  facts.forEach((f, i) => fact(slide, 0.65 + i * 4.05, 5.45, String(i + 1), f[0], f[1], f[2], { w: 3.1 }));
  finish(slide, 10,
    "Trust begins at ingestion. An immutable bronze envelope carries an event id, event time, sequence, source, schema version, and classification. Silver is the only deduplication and normalization contract, so batch and streaming converge.\nBad data remains visible in quarantine. The Event Hubs basic connector needs a shared key, so the architecture uses a managed-identity relay to a Custom Endpoint, isolated in a dedicated ingress workspace.",
    "Source cue | solution-architecture.md §4.1, ADR-005  •  deployment-topology.md §3",
  );
}

// 11 — four AI
{
  const slide = newSlide(11, "Intelligence with boundaries", "Four AI capabilities — Python decides; Foundry explains", "17:10–18:20", { dark: true, texture: true });
  const abilities = [
    ["RUL", "Lining remaining life", "physics-informed Python\nsilver thermal features", C.rust],
    ["ENE", "Energy dispatch", "deterministic optimizer\nhard constraints preserved", C.amber],
    ["QLT", "Quality risk", "genealogy model\nbounded what-if", C.teal],
    ["KNW", "Knowledge capture", "Speech + Foundry\ncited draft workflow", C.green],
  ];
  abilities.forEach((a, i) => {
    const x = 0.6 + i * 3.1;
    card(slide, x, 1.9, 2.7, 3.05, { dark: true, fill: C.coal, border: a[3], bar: a[3], lineWidth: 1 });
    circle(slide, x + 0.28, 2.27, 0.64, a[3], a[3]);
    tx(slide, a[0], x + 0.28, 2.51, 0.64, 0.09, { fontSize: 7.6, color: C.white, bold: true, align: "center" });
    tx(slide, a[1], x + 0.27, 3.05, 2.16, 0.2, { fontFace: F.head, fontSize: 12.5, color: C.white, bold: true });
    tx(slide, a[2], x + 0.27, 3.6, 2.15, 0.38, { fontSize: 8.7, color: C.steel, valign: "top" });
    tx(slide, "input  →  compute  →  human review", x + 0.27, 4.43, 2.16, 0.13, { fontSize: 6.9, color: a[3], bold: true, align: "center" });
  });
  roundRect(slide, 0.6, 5.62, 12.13, 0.65, C.coal, C.graphite, { lineWidth: 0.8 });
  badge(slide, 0.92, 5.82, "ADR-006", "guardrail");
  tx(slide, "Foundry retrieves, explains, and uses allow-listed tools. It does not calculate the authoritative answer, relax a constraint, or commit a decision.", 2.35, 5.84, 9.75, 0.15, { fontSize: 10.6, color: C.white, bold: true, align: "center" });
  finish(slide, 11,
    "There are four capabilities, governed by one rule: deterministic, testable Python services compute the authoritative result. Foundry is constrained to dialogue, retrieval, explanation, and named tools.\nAn LLM cannot invent a schedule, relax a hard constraint, or make a physical or financial commitment. That is ADR-006.",
    "Source cue | solution-architecture.md §4.2, ADR-006",
    true,
  );
}

// 12 — RUL
{
  const slide = newSlide(12, "AI deep dive 01", "Furnace lining remaining-useful-life: show uncertainty, retain the human", "18:20–20:35");
  badge(slide, 0.5, 1.3, "Synthetic evidence", "evidence");
  slide.addImage({ path: thermalMap, x: 0.55, y: 1.82, w: 5.38, h: 3.14 });
  addThermalLegend(slide, 1.05, 5.15);
  roundRect(slide, 6.33, 1.83, 2.8, 3.16, C.white, C.mist, { lineWidth: 0.8 });
  label(slide, 6.62, 2.12, "Synthetic RUL band", C.teal, 1.7);
  const bandX = 6.93;
  rect(slide, bandX, 3.27, 1.62, 0.15, C.paleTeal, C.paleTeal);
  line(slide, bandX, 3.35, 1.62, 0, C.teal, 3);
  [0, 0.5, 1].forEach((p) => line(slide, bandX + p * 1.62, 3.03, 0, 0.6, C.graphite, 0.7));
  circle(slide, bandX + 0.5 * 1.62 - 0.08, 3.17, 0.16, C.rust, C.rust);
  tx(slide, "16.8", bandX - 0.08, 3.73, 0.45, 0.11, { fontSize: 7.2, color: C.muted, align: "center" });
  tx(slide, "21.0", bandX + 0.56, 2.72, 0.5, 0.12, { fontSize: 8.3, color: C.rust, bold: true, align: "center" });
  tx(slide, "27.5", bandX + 1.3, 3.73, 0.45, 0.11, { fontSize: 7.2, color: C.muted, align: "center" });
  tx(slide, "P10", bandX - 0.01, 4.08, 0.31, 0.08, { fontSize: 6.2, color: C.muted, align: "center" });
  tx(slide, "P50", bandX + 0.62, 4.08, 0.31, 0.08, { fontSize: 6.2, color: C.muted, align: "center" });
  tx(slide, "P90", bandX + 1.32, 4.08, 0.31, 0.08, { fontSize: 6.2, color: C.muted, align: "center" });
  badge(slide, 6.66, 4.42, "Risk 0.87 | High", "evidence");
  roundRect(slide, 9.54, 1.83, 3.01, 3.16, C.coal, C.coal);
  label(slide, 9.84, 2.13, "Drivers", C.amber, 1.4);
  const drivers = [
    ["Heat-flux 6h slope", 0.82, C.rust],
    ["Spatial contrast", 0.66, C.amber],
    ["Cooling residual", 0.55, C.teal],
  ];
  drivers.forEach((d, i) => {
    const y = 2.74 + i * 0.63;
    tx(slide, d[0], 9.84, y, 1.55, 0.12, { fontSize: 7.4, color: C.mist, bold: true });
    roundRect(slide, 9.84, y + 0.24, 2.2, 0.16, C.graphite, C.graphite);
    roundRect(slide, 9.84, y + 0.24, 2.2 * d[1], 0.16, d[2], d[2]);
  });
  sourceBar(slide, 0.55, 5.75, 12, [
    { text: "Silver thermal/cooling features", color: C.teal },
    { text: "Physics-informed Python scorer", color: C.rust },
    { text: "Advisory → human acknowledgement", color: C.amber },
    { text: "Linked synthetic work order", color: C.green },
  ]);
  finish(slide, 12,
    "This model turns a surprise into a planned intervention. It is physics-informed, so it uses heat-flux and cooling relationships rather than fitting a black box. In the synthetic scenario, P50 is 21 days, with P10 16.8 and P90 27.5; I deliberately show the band.\nThe output is advisory only. A reliability engineer acknowledges it and links a synthetic work order; the platform does not actuate the furnace. Pilot scoring is daily, not a promised real-time feature.",
    "Source cue | demo-runbook.md §5  •  synthetic-data-and-simulators.md §8.1  •  solution-architecture.md §4.2",
  );
}

// 13 — energy dispatch
{
  const slide = newSlide(13, "AI deep dive 02", "Energy dispatch: feasible value, bounded by production reality", "20:35–22:20");
  badge(slide, 0.5, 1.3, "Synthetic evidence", "evidence");
  card(slide, 0.5, 1.85, 5.55, 3.72, { fill: C.white, border: C.mist, bar: C.amber });
  label(slide, 0.8, 2.12, "Day-ahead price signal", C.amber, 2);
  line(slide, 0.92, 4.8, 4.55, 0, C.graphite, 0.8);
  line(slide, 0.92, 2.78, 0, 2.02, C.graphite, 0.8);
  const curve = [0.42, 0.38, 0.43, 0.55, 0.48, 0.63, 0.82, 1.72, 1.58, 0.91, 0.66, 0.52];
  curve.forEach((v, i) => {
    if (i < curve.length - 1) {
      line(slide, 1.0 + i * 0.38, 4.68 - v, 0.38, curve[i] - curve[i + 1], i === 6 ? C.rust : C.amber, 1.8);
    }
  });
  rect(slide, 3.59, 2.98, 0.55, 1.8, C.paleRust, C.paleRust);
  tx(slide, "280\nEUR/MWh\nscarcity peak", 3.43, 2.48, 0.87, 0.38, { fontSize: 7.1, color: C.rust, bold: true, align: "center", valign: "mid" });
  tx(slide, "00", 0.8, 4.95, 0.3, 0.09, { fontSize: 6.2, color: C.muted });
  tx(slide, "12", 2.83, 4.95, 0.3, 0.09, { fontSize: 6.2, color: C.muted });
  tx(slide, "24", 5.25, 4.95, 0.3, 0.09, { fontSize: 6.2, color: C.muted });
  card(slide, 6.4, 1.85, 6.15, 3.72, { fill: C.coal, border: C.coal, bar: C.teal });
  label(slide, 6.72, 2.12, "Baseline vs optimized dispatch", C.teal, 3);
  ["Baseline", "Optimized"].forEach((r, i) => {
    const y = 2.78 + i * 1.1;
    tx(slide, r, 6.72, y + 0.22, 0.8, 0.1, { fontSize: 7.6, color: C.mist, bold: true });
    const blocks = i === 0
      ? [[0.02, 1.2, C.graphite], [1.3, 0.85, C.rust], [2.24, 1.3, C.graphite], [3.62, 0.88, C.amber]]
      : [[0.02, 1.2, C.graphite], [1.3, 1.25, C.graphite], [2.65, 1.3, C.teal], [4.03, 0.47, C.graphite]];
    blocks.forEach((b) => roundRect(slide, 7.76 + b[0], y, b[1], 0.54, b[2], b[2]));
  });
  badge(slide, 6.72, 5.03, "8–13% modeled cost cut", "evidence");
  tx(slide, "Equal tonnage  |  zero hard-constraint violations  |  3–7% lower peak", 9.12, 5.1, 3.08, 0.12, { fontSize: 7.7, color: C.steel, bold: true, align: "center" });
  const constraints = [
    ["Only eligible flexible loads move", C.teal],
    ["Soak time, delivery, capacity preserved", C.amber],
    ["Human accepts / modifies / rejects", C.rust],
  ];
  constraints.forEach((c, i) => fact(slide, 0.68 + i * 4.08, 5.9, String(i + 1), c[0], "", c[1], { w: 3.0 }));
  finish(slide, 13,
    "Energy is the fastest payback because it acts every day against price volatility. The optimizer shifts only eligible flexible loads; urgent coils and every hard production constraint stay fixed.\nThe synthetic evening-scarcity scenario yields an 8–13 percent modeled cost reduction, 3–7 percent lower peak, equal tonnage, and zero hard-constraint violations. That is synthetic evidence, not a realized saving. A human accepts, modifies, or rejects the proposal with a reason.",
    "Source cue | demo-runbook.md §5  •  synthetic-data-and-simulators.md §8.2  •  solution-architecture.md §4.2",
  );
}

// 14 — quality
{
  const slide = newSlide(14, "AI deep dive 03", "Quality: see drift early, keep the recipe under human control", "22:20–23:50");
  badge(slide, 0.5, 1.3, "Synthetic evidence", "evidence");
  label(slide, 0.55, 1.86, "Full genealogy", C.teal, 2);
  const genealogy = [
    ["Heat", "H-LUX-260725-0042", 0.55, 2.35, C.graphite],
    ["Slab", "SLAB-042", 2.76, 2.35, C.teal],
    ["Coil", "COIL-LUX-260725-017", 4.97, 2.35, C.amber],
    ["Sample", "S-017-4", 7.18, 2.35, C.rust],
    ["Shipment", "OEM traceability", 9.39, 2.35, C.green],
  ];
  genealogy.forEach((g, i) => {
    stage(slide, g[2], g[3], 1.68, 1.06, g[0], g[1], g[4], { titleSize: 8.8, detailSize: 6.7 });
    if (i < genealogy.length - 1) chevron(slide, g[2] + 1.73, 2.71, 0.28, 0.24, C.graphite);
  });
  card(slide, 0.55, 4.12, 5.55, 1.75, { fill: C.white, border: C.mist, bar: C.rust });
  label(slide, 0.82, 4.36, "Multivariate drift before lab fail", C.rust, 2.7);
  const drift = [0.24, 0.32, 0.37, 0.41, 0.53, 0.61, 0.74, 0.91];
  drift.forEach((v, i) => {
    if (i < drift.length - 1) line(slide, 1.06 + i * 0.52, 5.55 - v, 0.52, drift[i] - drift[i + 1], C.rust, 2);
  });
  line(slide, 1.0, 5.55, 4.35, 0, C.graphite, 0.6);
  tx(slide, "coiling temperature + force balance drift together", 1.05, 4.76, 4.35, 0.13, { fontSize: 7.3, color: C.muted, bold: true, align: "center" });
  card(slide, 6.45, 4.12, 5.67, 1.75, { fill: C.coal, border: C.coal, bar: C.amber });
  badge(slide, 6.76, 4.38, "Bounded what-if", "evidence");
  tx(slide, "Predicted first-pass yield", 6.78, 4.88, 2.1, 0.14, { fontSize: 8, color: C.steel, bold: true });
  tx(slide, "88%", 6.78, 5.18, 1.05, 0.34, { fontFace: F.head, fontSize: 22, color: C.white, bold: true, align: "center" });
  chevron(slide, 8.04, 5.24, 0.43, 0.24, C.amber);
  tx(slide, "95%", 8.72, 5.18, 1.05, 0.34, { fontFace: F.head, fontSize: 22, color: C.amber, bold: true, align: "center" });
  tx(slide, "Predicted—not measured. No automatic recipe or setpoint write.", 9.8, 5.1, 1.85, 0.25, { fontSize: 7.6, color: C.steel, bold: true, align: "center", valign: "mid" });
  finish(slide, 14,
    "Quality is about catching drift before the first lab failure and proving traceability heat-by-heat. The model detects coiling-temperature and force-balance drift, then traces the affected heat, slab, coil, sample, and shipment.\nThe synthetic bounded what-if takes predicted first-pass yield from about 88 to 95 percent. It is a recommendation only; nothing writes an automatic recipe or setpoint.",
    "Source cue | demo-runbook.md §5  •  synthetic-data-and-simulators.md §8.3  •  solution-architecture.md §4.2",
  );
}

// 15 — knowledge
{
  const slide = newSlide(15, "AI deep dive 04", "Knowledge capture: preserve expertise without publishing a hallucination", "23:50–25:35", { dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Consent-aware workflow", "guardrail");
  const steps = [
    ["1", "CONSENT", "fictional / consented\nsynthetic persona", C.rust],
    ["2", "SPEECH", "Fast Transcription\nspeaker + confidence", C.amber],
    ["3", "EXTRACT", "trigger • check • rationale\nsafety boundary • citations", C.teal],
    ["4", "DRAFT", "expert review required\nnot operational instruction", C.green],
  ];
  steps.forEach((s, i) => {
    const x = 0.7 + i * 3.12;
    card(slide, x, 2.05, 2.57, 2.9, { dark: true, fill: C.coal, border: s[3], bar: s[3], lineWidth: 0.9 });
    circle(slide, x + 0.82, 2.45, 0.9, s[3], s[3]);
    tx(slide, s[0], x + 0.82, 2.78, 0.9, 0.13, { fontFace: F.head, fontSize: 15, color: C.white, bold: true, align: "center" });
    tx(slide, s[1], x + 0.22, 3.65, 2.1, 0.18, { fontFace: F.head, fontSize: 12, color: C.white, bold: true, align: "center" });
    tx(slide, s[2], x + 0.24, 4.15, 2.08, 0.33, { fontSize: 8.6, color: C.steel, bold: true, align: "center", valign: "mid" });
    if (i < steps.length - 1) chevron(slide, x + 2.67, 3.26, 0.27, 0.32, C.graphite);
  });
  roundRect(slide, 0.7, 5.64, 12, 0.62, C.coal, C.graphite, { lineWidth: 0.7 });
  tx(slide, "The draft cannot publish. A Knowledge Engineer edits, approves, and versions it before it enters general retrieval.", 1.0, 5.86, 11.36, 0.14, { fontSize: 10.6, color: C.white, bold: true, align: "center" });
  finish(slide, 15,
    "The goal is to preserve judgement before it retires. A consented interview is transcribed with speaker labels and confidence. The Foundry agent produces a structured, cited draft: trigger, observation, recommended check, rationale, and safety boundary.\nThe crucial guardrail is visible: the draft cannot publish. A Knowledge Engineer approves, edits, or rejects it. In the demo the operator is fictional and all voice/transcript content is synthetic.",
    "Source cue | solution-architecture.md §4.3  •  demo-runbook.md §7  •  security-governance-and-threat-model.md §13",
    true,
  );
}

// 16 — Responsible AI
{
  const slide = newSlide(16, "Governance by design", "Responsible AI: enforceable controls, not a policy poster", "25:35–27:55");
  badge(slide, 0.5, 1.3, "High-risk-adjacent posture", "guardrail");
  const stack = [
    ["Legal classification", "EU AI Act gate before non-synthetic processing", C.rust],
    ["RAI review board", "Data Science • DPO/Compliance • OT/ICS • Maintenance", C.amber],
    ["Human oversight", "approval event is independent of the model response", C.teal],
    ["Evidence & audit", "input • version • confidence • rationale • outcome", C.green],
  ];
  stack.forEach((s, i) => {
    const x = 0.55 + i * 2.93;
    const y = 2.05 + (3 - i) * 0.34;
    roundRect(slide, x, y, 2.55, 2.5 - i * 0.23, C.white, s[2], { lineWidth: 1.1 });
    rect(slide, x, y, 2.55, 0.12, s[2], s[2]);
    tx(slide, s[0], x + 0.2, y + 0.43, 2.15, 0.24, { fontFace: F.head, fontSize: 11.4, color: C.ink, bold: true, align: "center" });
    tx(slide, s[1], x + 0.2, y + 1.13, 2.15, 0.46, { fontSize: 8.3, color: C.muted, align: "center", valign: "mid" });
  });
  line(slide, 1.82, 5.55, 9.18, 0, C.graphite, 1.2);
  tx(slide, "AI governance is continuous — from design classification through an auditable outcome.", 2.0, 5.75, 8.9, 0.15, { fontSize: 10, color: C.ink, bold: true, align: "center" });
  roundRect(slide, 9.9, 1.88, 2.65, 3.32, C.coal, C.coal);
  label(slide, 10.18, 2.16, "Prompt-injection defense", C.amber, 1.92);
  const shields = [
    ["Treat payloads as untrusted", C.rust],
    ["Prompt Shields: direct + indirect", C.amber],
    ["Instruction / data separation", C.teal],
    ["Narrow tool allow-lists + audit", C.green],
  ];
  shields.forEach((s, i) => {
    circle(slide, 10.2, 2.72 + i * 0.52, 0.25, s[1], s[1]);
    tx(slide, "✓", 10.2, 2.8 + i * 0.52, 0.25, 0.06, { fontSize: 6.1, color: C.white, bold: true, align: "center" });
    tx(slide, s[0], 10.58, 2.74 + i * 0.52, 1.65, 0.16, { fontSize: 7.1, color: C.mist, bold: true, valign: "mid" });
  });
  finish(slide, 16,
    "We take a conservative high-risk-adjacent posture while Legal and Compliance determine the formal EU AI Act classification. A cross-functional Responsible AI review board signs off before non-synthetic production.\nOn GenAI, every retrieved document and market payload is untrusted. Prompt Shields, instruction/data separation, allow-listed tools, audit, and independent human approval keep a model response from becoming authorization.",
    "Source cue | security-governance-and-threat-model.md §12, §15–16  •  solution-architecture.md ADR-006/007",
  );
}

// 17 — Security, identity, residency
{
  const slide = newSlide(17, "Security and residency", "Zero Trust across identities, data classes, and EU placement", "27:55–30:00", { dark: true, texture: true });
  badge(slide, 0.5, 1.3, "No standing secrets", "guardrail");
  circle(slide, 4.8, 2.38, 2.26, C.coal, C.teal, { lineWidth: 2.3 });
  circle(slide, 5.42, 3.0, 1.02, C.teal, C.teal);
  tx(slide, "ENTRA\nZERO TRUST", 5.5, 3.3, 0.86, 0.2, { fontFace: F.head, fontSize: 9.4, color: C.white, bold: true, align: "center" });
  const ids = [
    ["Human\npersona", 2.98, 2.25, C.rust],
    ["OT\nGateway MI", 7.0, 2.22, C.amber],
    ["Relay\nMI", 2.98, 4.82, C.teal],
    ["BFF / Worker\nMIs", 7.0, 4.82, C.green],
  ];
  ids.forEach((id) => {
    circle(slide, id[1], id[2], 1.0, C.coal, id[3], { lineWidth: 1.4 });
    tx(slide, id[0], id[1] + 0.08, id[2] + 0.35, 0.84, 0.2, { fontSize: 7.2, color: C.white, bold: true, align: "center" });
    line(slide, 4.05 + (id[1] < 4 ? 0 : 1.93), 3.47 + (id[2] > 3 ? 0.53 : -0.53), (id[1] < 4 ? 0.65 : -0.65), (id[2] > 3 ? -0.32 : 0.32), C.graphite, 1);
  });
  card(slide, 9.55, 1.86, 2.75, 3.68, { dark: true, fill: C.coal, border: C.graphite, bar: C.amber });
  label(slide, 9.84, 2.18, "EU residency posture", C.amber, 1.85);
  tx(slide, "SWEDEN\nCENTRAL", 9.84, 2.72, 2.1, 0.43, { fontFace: F.head, fontSize: 19, color: C.white, bold: true, align: "center" });
  tx(slide, "Fabric • Event Hubs • apps\nFoundry project • Speech", 9.84, 3.36, 2.1, 0.27, { fontSize: 8.3, color: C.steel, bold: true, align: "center" });
  badge(slide, 9.96, 4.03, "Data Zone (EU)", "evidence");
  tx(slide, "EU-zone does not imply Sweden-only inference.\nSingle-region policy needs regional deployment validation.", 9.84, 4.53, 2.1, 0.43, { fontSize: 7.2, color: C.steel, align: "center" });
  sourceBar(slide, 0.7, 5.91, 8.1, [
    { text: "Azure RBAC", color: C.rust },
    { text: "Fabric + OneLake roles", color: C.teal },
    { text: "Foundry RBAC", color: C.amber },
    { text: "App roles", color: C.green },
  ]);
  finish(slide, 17,
    "Security uses Zero Trust and separate workload identities. Azure RBAC, Fabric and OneLake roles, Foundry RBAC, and app roles are distinct authorization planes. The browser never receives a workload credential.\nThe primary placement is Sweden Central. Foundry Data Zone EU keeps processing within the EU zone but is not a Sweden-only guarantee; if policy requires that, the deployment type must change and be validated.",
    "Source cue | solution-architecture.md §8  •  deployment-topology.md §2  •  security-governance-and-threat-model.md",
    true,
  );
}

// 18 — synthetic realism
{
  const slide = newSlide(18, "Evidence discipline", "Synthetic data: deterministic, physics-first, visibly labeled", "30:00–31:45");
  badge(slide, 0.5, 1.3, "Synthetic evidence", "evidence");
  const flow = [
    ["SIGNED\nMANIFEST", "root seed 240725\nchecksum", C.graphite],
    ["PROCESS +\nTRUTH LEDGER", "hidden state\ninjected anomalies", C.rust],
    ["CONTRACT +\nPHYSICS VALIDATOR", "units, ordering,\nmass/energy", C.amber],
    ["PUBLISH /\nREPLAY", "same event envelope\nfallback pack", C.teal],
  ];
  flow.forEach((f, i) => {
    const x = 0.56 + i * 3.13;
    stage(slide, x, 2.04, 2.61, 1.55, f[0], f[1], f[2], { titleSize: 11.4, detailSize: 8.3 });
    if (i < flow.length - 1) chevron(slide, x + 2.69, 2.57, 0.28, 0.35, C.graphite);
  });
  const assertions = [
    ["PHYSICS FIRST", "Process state is simulated before modeled sensors observe it.", C.rust],
    ["REPRODUCIBLE", "Child seed = SHA-256(root | scenario | plant | asset | signal).", C.teal],
    ["VISIBLE BOUNDARY", "Every record: SYNTHETIC / DEMO-NONPERSONAL.", C.amber],
  ];
  assertions.forEach((a, i) => {
    const x = 0.56 + i * 4.1;
    card(slide, x, 4.36, 3.73, 1.26, { fill: C.white, border: C.mist, bar: a[2] });
    tx(slide, a[0], x + 0.2, 4.64, 3.2, 0.14, { fontSize: 8, color: a[2], bold: true, charSpacing: 0.8 });
    tx(slide, a[1], x + 0.2, 5.0, 3.18, 0.28, { fontSize: 8.2, color: C.ink, bold: true, valign: "mid" });
  });
  sourceBar(slide, 0.56, 6.08, 12, [
    { text: "21-day warning | seed 240726", color: C.rust },
    { text: "Evening energy spike | seed 240727", color: C.amber },
    { text: "Quality drift | seed 240728", color: C.teal },
    { text: "Outage / recovery | seed 240729", color: C.green },
  ]);
  finish(slide, 18,
    "Synthetic is credible only with disciplined design. One root seed produces stable child seeds. A process simulator creates hidden state, then modeled sensors observe it; mass and energy balance, lining wear, and RUL constraints remain physically plausible.\nA truth ledger records anomalies and expected outcomes. Contract, physics, and scenario validation must pass before the run is presentable. All records are visibly synthetic and cannot mix with production.",
    "Source cue | synthetic-data-and-simulators.md §1, §4, §6, §8–10",
  );
}

// 19 — cost and scale
{
  const slide = newSlide(19, "Delivery posture", "Start small, measure honestly, scale only after gates", "31:45–33:30");
  badge(slide, 0.5, 1.3, "Cost + region + scale", "context");
  const phases = [
    ["DEMO", "Synthetic defense", "F2 baseline\nreproducible demo", C.graphite],
    ["PHASE 1", "One-site shadow pilot", "read-only real feeds\nmeasure outcomes", C.teal],
    ["PHASE 2+", "Four-site production scale", "human-approved writes\nafter gates", C.rust],
  ];
  phases.forEach((p, i) => {
    const x = 0.52 + i * 4.1;
    card(slide, x, 1.88, 3.65, 1.9, { fill: C.white, border: C.mist, bar: p[3] });
    badge(slide, x + 0.22, 2.12, p[0], i === 0 ? "context" : i === 1 ? "evidence" : "target");
    tx(slide, p[1], x + 0.22, 2.65, 3.0, 0.21, { fontFace: F.head, fontSize: 13, color: C.ink, bold: true });
    tx(slide, p[2], x + 0.22, 3.14, 2.95, 0.26, { fontSize: 8.4, color: C.muted, bold: true, valign: "mid" });
    if (i < phases.length - 1) chevron(slide, x + 3.75, 2.64, 0.28, 0.35, C.graphite);
  });
  card(slide, 0.52, 4.25, 5.9, 1.86, { fill: C.coal, border: C.coal, bar: C.amber });
  label(slide, 0.82, 4.55, "Capacity cost control", C.amber, 2);
  tx(slide, "F2", 0.83, 4.95, 0.77, 0.35, { fontFace: F.head, fontSize: 23, color: C.white, bold: true, align: "center" });
  chevron(slide, 1.74, 5.05, 0.38, 0.25, C.amber);
  tx(slide, "F4", 2.34, 4.95, 0.77, 0.35, { fontFace: F.head, fontSize: 23, color: C.amber, bold: true, align: "center" });
  tx(slide, "Only after measured contention.\nNever F64 merely for viewer licensing.", 3.4, 4.87, 2.42, 0.38, { fontSize: 8.4, color: C.steel, bold: true, align: "center", valign: "mid" });
  card(slide, 6.65, 4.25, 5.9, 1.86, { fill: C.white, border: C.mist, bar: C.rust });
  label(slide, 6.95, 4.55, "Lifecycle + recovery", C.rust, 2);
  tx(slide, "01:00", 6.97, 4.95, 1.05, 0.3, { fontFace: F.head, fontSize: 19, color: C.rust, bold: true, align: "center" });
  tx(slide, "Europe/Luxembourg non-prod pause check\nProduction is never auto-paused.", 8.15, 4.82, 3.78, 0.25, { fontSize: 8.3, color: C.ink, bold: true, align: "center", valign: "mid" });
  tx(slide, "Sweden Central primary  |  West Europe = tested recovery target, not automatic failover", 7.0, 5.55, 5.15, 0.15, { fontSize: 7.4, color: C.muted, bold: true, align: "center" });
  finish(slide, 19,
    "We begin with a cost-conscious F2 demo capacity and move to F4 only after measurable contention. There is no invented euro-per-hour price; the cost figure needs regional pricing and pilot measurement.\nA 01:00 Europe/Luxembourg lifecycle check pauses only non-production capacity when safe; production is hard-denied. Sweden Central is primary. West Europe is a recovery target to validate, not automatic Fabric failover.",
    "Source cue | deployment-topology.md §2, §5–7  •  operations-and-cost.md §8–9",
  );
}

// 20 — demo handoff
{
  const slide = newSlide(20, "Demo handoff", "Now the proof: a 10-minute deterministic persona journey", "33:30–35:00", { dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Live demo next", "evidence");
  tx(slide, "SYNTHETIC DEMO DATA — NOT FOR OPERATIONAL CONTROL", 0.5, 1.86, 12.25, 0.32, { fontFace: F.head, fontSize: 18.5, color: C.white, bold: true, align: "center" });
  roundRect(slide, 5.45, 2.45, 2.43, 1.2, C.rust, C.rust);
  tx(slide, "10:00", 5.58, 2.67, 2.17, 0.39, { fontFace: F.head, fontSize: 28, color: C.white, bold: true, align: "center" });
  tx(slide, "presenter timer", 5.58, 3.19, 2.17, 0.12, { fontSize: 8, color: C.paleRust, bold: true, align: "center" });
  const tabs = [
    ["Fleet", "00:00", C.rust],
    ["Fabric core", "00:40", C.teal],
    ["Energy", "01:20", C.amber],
    ["RUL", "03:00", C.rust],
    ["Quality", "04:40", C.teal],
    ["Knowledge", "06:20", C.green],
    ["Audit", "08:00", C.graphite],
  ];
  tabs.forEach((t, i) => {
    const x = 0.5 + i * 1.78;
    stage(slide, x, 4.42, 1.5, 0.92, t[0], t[1], t[2], { dark: true, fill: C.coal, titleSize: 8.8, detailSize: 7, border: t[2] });
    if (i < tabs.length - 1) chevron(slide, x + 1.53, 4.71, 0.17, 0.19, C.graphite);
  });
  tx(slide, "Seed 240725  |  60× accelerated clock  |  every screen synthetic  |  fallback after 10 seconds", 1.18, 5.9, 10.95, 0.15, { fontSize: 9.1, color: C.steel, bold: true, align: "center" });
  finish(slide, 20,
    "Now I will show the platform live. The scenario is deterministic: seed 240725, a 60-times accelerated clock, and synthetic labels on every screen. We move through fleet, Fabric core, energy, lining, quality, knowledge, and audit.\nIf a live element hesitates, I will use a cached deterministic result rather than debug in front of you. Start the 10-minute timer and switch to the Plant Manager tab.",
    "Source cue | demo-runbook.md §3–4  •  oral-defense-and-slide-plan.md §3",
    true,
  );
}

// 21 — backup target/evidence
{
  const slide = newSlide(21, "FAQ backup", "Are the 14 / 22 / 21 / 8 figures proven?", "", { backup: true });
  badge(slide, 0.5, 1.3, "Answer discipline", "backup");
  card(slide, 0.55, 1.95, 5.72, 3.45, { fill: C.paleAmber, border: C.amber, bar: C.amber });
  badge(slide, 0.85, 2.28, "Target", "target");
  tx(slide, "FALSIFIABLE BUSINESS\nAMBITION", 0.85, 2.85, 4.85, 0.44, { fontFace: F.head, fontSize: 21, color: C.ink, bold: true });
  tx(slide, "14% energy  •  22% CO₂  •  21-day warning  •  8% yield\nEach has a stated baseline; each must be proven in a one-site pilot.", 0.85, 3.72, 4.78, 0.36, { fontSize: 10.2, color: C.ink, bold: true, valign: "mid" });
  card(slide, 7.02, 1.95, 5.72, 3.45, { fill: C.paleTeal, border: C.teal, bar: C.teal });
  badge(slide, 7.32, 2.28, "Evidence", "evidence");
  tx(slide, "REPRODUCIBLE SYNTHETIC\nMECHANICS", 7.32, 2.85, 4.85, 0.44, { fontFace: F.head, fontSize: 21, color: C.ink, bold: true });
  tx(slide, "RUL uncertainty • feasible dispatch • quality what-if • audit trail\nThe demo proves mechanics—not banked production savings.", 7.32, 3.72, 4.78, 0.36, { fontSize: 10.2, color: C.ink, bold: true, valign: "mid" });
  roundRect(slide, 0.55, 5.85, 12.19, 0.47, C.coal, C.coal);
  tx(slide, "FAQ answer: “That is a validation gate, not a claim.” The audit ledger turns a target into a measured outcome.", 0.9, 6.03, 11.5, 0.12, { fontSize: 9.3, color: C.white, bold: true, align: "center" });
  finish(slide, 21,
    "No. The 14, 22, 21, and 8 figures are targets, each with a baseline. The demo demonstrates reproducible synthetic mechanics, not realized business savings.\nA one-site pilot uses an auditable savings ledger to connect recommendation, counterfactual, human decision, and realized outcome. If a number has not been measured, call it a validation gate.",
    "FAQ A | faq.md Q1–Q4  •  oral-defense-and-slide-plan.md §6",
  );
}

// 22 — backup Fabric
{
  const slide = newSlide(22, "FAQ backup", "Why Fabric — and why not a parallel lake, Databricks, or Snowflake?", "", { backup: true, dark: true, texture: true });
  badge(slide, 0.5, 1.3, "ADR-001 / ADR-002", "backup");
  const compare = [
    ["HOT CLOCK", "Eventstream + Eventhouse/KQL\nfresh operations, alarms, investigation", C.rust],
    ["GOVERNED CLOCK", "OneLake bronze → silver → gold\nhistory, lineage, training, KPIs", C.teal],
    ["ONE SEMANTIC TRUTH", "Direct Lake + Power BI\nno copied KPI definition", C.amber],
  ];
  compare.forEach((c, i) => {
    const x = 0.7 + i * 4.1;
    card(slide, x, 2.05, 3.5, 2.3, { dark: true, fill: C.coal, border: c[2], bar: c[2], lineWidth: 1 });
    tx(slide, c[0], x + 0.25, 2.55, 2.95, 0.17, { fontFace: F.head, fontSize: 13, color: C.white, bold: true, align: "center" });
    tx(slide, c[1], x + 0.25, 3.23, 2.95, 0.4, { fontSize: 9, color: C.steel, bold: true, align: "center", valign: "mid" });
  });
  line(slide, 2.4, 4.8, 8.42, 0, C.graphite, 1.2);
  tx(slide, "One governed estate gives fewer copies, fewer trust boundaries, and one lineage graph for audit.", 1.5, 5.15, 10.4, 0.19, { fontSize: 13, color: C.white, bold: true, align: "center" });
  finish(slide, 22,
    "Fabric is central because we need two clocks in one governed estate: fresh operational telemetry and durable, governed history. Eventhouse KQL is purpose-built for the former; OneLake Delta for the latter; Direct Lake keeps one semantic KPI definition.\nDatabricks, Snowflake, or a custom lake can store data, but would require stitching together multiple services and copies. ADR-001 rejects that parallel estate; ADR-002 keeps KQL distinct from Delta.",
    "FAQ B/C | faq.md Q6–Q14  •  solution-architecture.md ADR-001/002",
    true,
  );
}

// 23 — backup regions
{
  const slide = newSlide(23, "FAQ backup", "Where is data processed — and what remains a validation gate?", "", { backup: true });
  badge(slide, 0.5, 1.3, "Regions + residency", "backup");
  const places = [
    ["Sweden Central", "Fabric • Event Hubs • apps\nFoundry project • Speech", C.teal],
    ["Data Zone (EU)", "Normal Foundry inference\nEU zone, not Sweden-only", C.amber],
    ["Regional deployment", "If legal policy requires\nSweden-only processing", C.rust],
    ["West Europe", "Recovery target to test\nnever automatic replica", C.graphite],
  ];
  places.forEach((p, i) => {
    const x = 0.6 + (i % 2) * 6.15;
    const y = 1.95 + Math.floor(i / 2) * 2.02;
    card(slide, x, y, 5.62, 1.55, { fill: C.white, border: C.mist, bar: p[2] });
    circle(slide, x + 0.28, y + 0.45, 0.52, p[2], p[2]);
    tx(slide, String(i + 1), x + 0.28, y + 0.62, 0.52, 0.07, { fontSize: 7.2, color: C.white, bold: true, align: "center" });
    tx(slide, p[0], x + 1.03, y + 0.35, 3.95, 0.18, { fontFace: F.head, fontSize: 12.5, color: C.ink, bold: true });
    tx(slide, p[1], x + 1.03, y + 0.78, 3.95, 0.25, { fontSize: 8.2, color: C.muted, bold: true });
  });
  roundRect(slide, 0.6, 6.12, 12.05, 0.35, C.paleRust, C.rust, { lineWidth: 0.5 });
  tx(slide, "No automatic Fabric BCDR claim. Tenant quota, model/tool support, Speech features, and recovery must be evidenced before deployment.", 0.82, 6.25, 11.6, 0.09, { fontSize: 7.6, color: C.ink, bold: true, align: "center" });
  finish(slide, 23,
    "The target architecture is EU-only with Sweden Central primary. Foundry's Data Zone EU maintains EU-zone processing but does not guarantee every inference stays in Sweden Central. A single-region policy requires a regional deployment and validation of model and quota.\nWest Europe is an EU recovery target that requires approval and a tested restore. We do not promise automatic cross-region Fabric failover.",
    "FAQ E | faq.md Q21–Q24  •  deployment-topology.md §2  •  azure-ai-regions.md",
  );
}

// 24 — backup security and AI safety
{
  const slide = newSlide(24, "FAQ backup", "What prevents an LLM, identity, or OT boundary from causing harm?", "", { backup: true, dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Security + AI safety", "backup");
  const gates = [
    ["No OT control", "No cloud-initiated plant session; no PLC / interlock / setpoint write.", C.rust],
    ["Python authority", "LLM explains/retrieves only; cannot calculate, relax, or commit.", C.amber],
    ["Untrusted content", "Prompt Shields, separation, allow-listed tools, full audit.", C.teal],
    ["Separate planes", "Azure RBAC ≠ Fabric roles ≠ Foundry RBAC ≠ app roles.", C.green],
  ];
  gates.forEach((g, i) => {
    const x = 0.67 + (i % 2) * 6.16;
    const y = 1.98 + Math.floor(i / 2) * 2.05;
    card(slide, x, y, 5.62, 1.54, { dark: true, fill: C.coal, border: g[2], bar: g[2], lineWidth: 0.9 });
    circle(slide, x + 0.28, y + 0.43, 0.56, g[2], g[2]);
    tx(slide, "✓", x + 0.28, y + 0.63, 0.56, 0.08, { fontSize: 10, color: C.white, bold: true, align: "center" });
    tx(slide, g[0], x + 1.08, y + 0.31, 3.95, 0.17, { fontFace: F.head, fontSize: 12.2, color: C.white, bold: true });
    tx(slide, g[1], x + 1.08, y + 0.77, 3.95, 0.26, { fontSize: 8.3, color: C.steel, bold: true });
  });
  finish(slide, 24,
    "Safety comes from architecture rather than model confidence. The OT boundary is outbound-only; Python is authoritative for math; retrieved content is untrusted; and identities are deliberately separated across authorization planes.\nThe GenAI agent has only read, forecast, simulate, and propose tools. A response is never authorization, and human approval stays independently enforced.",
    "FAQ F/G | faq.md Q25–Q36  •  security-governance-and-threat-model.md",
    true,
  );
}

// 25 — backup operations and scale
{
  const slide = newSlide(25, "FAQ backup", "How does it operate, control cost, and scale to four countries?", "", { backup: true });
  badge(slide, 0.5, 1.3, "Operations + scale", "backup");
  const rows = [
    ["Capacity", "F2 initial; F4 only after measured contention. No invented price or F64 licensing shortcut.", C.amber],
    ["Lifecycle", "01:00 Europe/Luxembourg non-prod pause check; readiness verified on resume; prod hard-denied.", C.rust],
    ["Resilience", "Live cloud → local replay → cached interactive → recording → static proof pack.", C.teal],
    ["Scale", "Same versioned event/API contract; per-plant gateway, Event Hub authorization, relay, measured capacity.", C.green],
  ];
  rows.forEach((r, i) => {
    const y = 1.88 + i * 1.08;
    card(slide, 0.6, y, 12.1, 0.8, { fill: C.white, border: C.mist, bar: r[2] });
    tx(slide, r[0].toUpperCase(), 0.93, y + 0.3, 1.4, 0.13, { fontSize: 8.6, color: r[2], bold: true, charSpacing: 0.9 });
    tx(slide, r[1], 2.45, y + 0.22, 9.65, 0.2, { fontSize: 9.8, color: C.ink, bold: true, valign: "mid" });
  });
  roundRect(slide, 0.6, 6.3, 12.1, 0.26, C.coal, C.coal);
  tx(slide, "No automatic production pause • no untested automatic cross-region failover • no production euro/hour claim before measurement", 0.86, 6.385, 11.58, 0.075, { fontSize: 6.8, color: C.white, bold: true, align: "center" });
  finish(slide, 25,
    "The design starts economically with F2, moves to F4 only after measurement, and quotes no price before a Sweden Central sizing exercise. The 01:00 lifecycle check is non-production only and never shuts down an active rehearsal.\nScaling is contract-first: each plant gets a gateway, authorization, and relay, while the core event and API contracts remain stable. The rehearsed fallback ladder keeps the demo and operations explainable under failure.",
    "FAQ D/K/L | faq.md Q16–Q20, Q48–Q53  •  operations-and-cost.md",
  );
}

// 26 — backup limitations
{
  const slide = newSlide(26, "FAQ backup", "What are the honest limitations and release gates?", "", { backup: true, dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Candor", "backup");
  const limits = [
    ["SYNTHETIC ONLY", "Headline outcomes remain targets, not field results.", C.rust],
    ["DAILY RUL", "Pilot scoring is daily; near-real-time is a measured later enhancement.", C.amber],
    ["CONTRIBUTOR SCOPE", "Custom Endpoint publisher role is isolated, not eliminated.", C.teal],
    ["NO AUTO BCDR", "Sweden Central recovery needs a tested EU restore design.", C.green],
  ];
  limits.forEach((l, i) => {
    const x = 0.66 + (i % 2) * 6.2;
    const y = 1.92 + Math.floor(i / 2) * 1.62;
    card(slide, x, y, 5.64, 1.13, { dark: true, fill: C.coal, border: l[2], bar: l[2], lineWidth: 0.9 });
    tx(slide, l[0], x + 0.28, y + 0.27, 2.1, 0.13, { fontSize: 8.1, color: l[2], bold: true, charSpacing: 0.8 });
    tx(slide, l[1], x + 0.28, y + 0.65, 4.8, 0.18, { fontSize: 8.3, color: C.steel, bold: true });
  });
  tx(slide, "PRODUCTION GATES", 0.68, 5.55, 2.4, 0.15, { fontFace: F.head, fontSize: 11, color: C.white, bold: true });
  const gates = ["Tenant quota / feature proof", "Custom Endpoint identity", "DPO / legal / AI Act", "OT vendor + DMZ sign-off", "Market licence + freshness", "Capacity / DR / security acceptance"];
  gates.forEach((g, i) => {
    const x = 0.68 + (i % 3) * 4.08;
    const y = 5.95 + Math.floor(i / 3) * 0.35;
    circle(slide, x, y, 0.16, C.rust, C.rust);
    tx(slide, g, x + 0.26, y + 0.02, 3.4, 0.08, { fontSize: 6.85, color: C.steel, bold: true });
  });
  finish(slide, 26,
    "The honest limitations are visible: all data is synthetic, pilot RUL scoring is daily, the Custom Endpoint Contributor scope is mitigated by isolation rather than solved, and Sweden Central has no automatic BCDR promise.\nProduction needs tenant feature proof, Custom Endpoint and query-adapter identity validation, DPO and legal decisions, OT approval, market-data licensing, capacity and DR testing, and all security acceptance gates.",
    "FAQ M | faq.md Q54–Q57  •  validation-report.md §Remaining production gates",
    true,
  );
}

// 27 — backup: the advisory boundary
{
  const slide = newSlide(27, "FAQ backup", "Why we do not write to the furnace", "", { backup: true });
  badge(slide, 0.5, 1.3, "Scope defense", "guardrail", 1.45);
  tx(slide, "The advisory boundary is a designed acceptance criterion (O1, C-04, AI-05) — not a missing feature.", 2.08, 1.335, 7.4, 0.18, {
    fontSize: 8.4, color: C.muted, bold: true,
  });

  label(slide, 0.5, 1.78, "ISA-95 / Purdue placement", C.muted, 3.4);

  card(slide, 0.5, 1.99, 6.15, 0.86, { fill: C.white, border: C.teal, bar: C.teal });
  tx(slide, "L4 / L3 — BUSINESS, MES, HISTORIAN", 0.72, 2.14, 4.3, 0.12, {
    fontSize: 7.4, color: C.teal, bold: true, charSpacing: 0.9,
  });
  roundRect(slide, 5.42, 2.09, 1.02, 0.24, C.paleTeal, C.teal, { lineWidth: 0.5 });
  tx(slide, "WE LIVE HERE", 5.47, 2.175, 0.92, 0.09, { fontSize: 6.2, color: C.teal, bold: true, align: "center" });
  tx(slide, "NovaSteel: Fabric core, four AI capabilities, persona apps, human approval", 0.72, 2.46, 5.55, 0.28, {
    fontSize: 9.4, color: C.ink, bold: true, valign: "top",
  });

  roundRect(slide, 0.5, 2.98, 6.15, 0.72, C.coal, C.rust, { lineWidth: 1.3 });
  tx(slide, "OT / IT BOUNDARY  —  IEC 62443 ZONE CONDUIT", 0.72, 3.10, 5.7, 0.1, {
    fontSize: 7, color: C.amber, bold: true, charSpacing: 1.1,
  });
  slide.addShape(S.upArrow, { x: 0.74, y: 3.32, w: 0.19, h: 0.28, fill: { color: C.teal }, line: { color: C.teal, width: 0.5 } });
  tx(slide, "TELEMETRY UP  ·  read-only historian / OPC UA tags", 1.03, 3.395, 2.5, 0.1, {
    fontSize: 7.2, color: C.mist, bold: true,
  });
  slide.addShape(S.downArrow, { x: 3.66, y: 3.32, w: 0.19, h: 0.28, fill: { color: C.rust }, line: { color: C.rust, width: 0.5 } });
  tx(slide, "NO COMMAND DOWN  ·  no setpoint, no PLC write", 3.95, 3.395, 2.5, 0.1, {
    fontSize: 7.2, color: C.paleRust, bold: true,
  });

  card(slide, 0.5, 3.80, 6.15, 1.88, { fill: C.paleSteel, border: C.steel, bar: C.graphite });
  const otLevels = [
    ["L2", "Supervisory control — SCADA / HMI", "operator authority stays on the floor"],
    ["L1", "Regulatory control — PLC / DCS setpoints", "vendor-certified control logic"],
    ["L0", "Sensors, actuators, SIS interlocks", "IEC 61511 safety-instrumented functions"],
  ];
  otLevels.forEach((lvl, i) => {
    const y = 3.92 + i * 0.56;
    roundRect(slide, 0.72, y, 5.71, 0.5, C.white, C.mist, { lineWidth: 0.5 });
    roundRect(slide, 0.85, y + 0.13, 0.42, 0.24, C.graphite, C.graphite, { lineWidth: 0.4 });
    tx(slide, lvl[0], 0.9, y + 0.215, 0.32, 0.09, { fontSize: 7, color: C.white, bold: true, align: "center" });
    tx(slide, lvl[1], 1.4, y + 0.115, 3.65, 0.12, { fontSize: 8.7, color: C.ink, bold: true });
    tx(slide, lvl[2], 1.4, y + 0.31, 3.65, 0.1, { fontSize: 6.8, color: C.muted });
    roundRect(slide, 5.22, y + 0.14, 1.06, 0.22, C.paleRust, C.rust, { lineWidth: 0.5 });
    tx(slide, "NO WRITE", 5.27, y + 0.222, 0.96, 0.08, { fontSize: 6.3, color: C.oxide, bold: true, align: "center" });
  });

  label(slide, 7.05, 1.78, "Not read-only — the platform writes decisions", C.muted, 5.4);
  const writes = [
    ["Energy dispatch decision", "POST /v1/energy/recommendations/{id}:approve", C.teal],
    ["Maintenance work order", "POST /v1/workorders  —  from a lining-wear alert", C.amber],
    ["Procedure publication", "POST /v1/knowledge/procedures/{id}:approve", C.green],
    ["Immutable decision record", "GET /v1/audit/decisions  —  hash-chained trail", C.rust],
  ];
  writes.forEach((wr, i) => {
    const y = 1.99 + i * 0.79;
    card(slide, 7.05, y, 5.78, 0.68, { fill: C.white, border: C.mist, bar: wr[2] });
    circle(slide, 7.28, y + 0.21, 0.26, wr[2], wr[2]);
    tx(slide, "✓", 7.28, y + 0.305, 0.26, 0.08, { fontSize: 7.4, color: C.white, bold: true, align: "center" });
    tx(slide, wr[0], 7.68, y + 0.13, 4.9, 0.13, { fontSize: 9.2, color: C.ink, bold: true });
    tx(slide, wr[1], 7.68, y + 0.4, 4.9, 0.11, { fontSize: 7.1, color: C.muted, fontFace: F.mono });
  });

  card(slide, 7.05, 5.16, 5.78, 0.62, { fill: C.paleAmber, border: C.amber, bar: C.amber });
  tx(slide, "PHASE 2 — guarded write-back to CMMS / MES only: human-approved, threshold-bounded, reversible. Never a direct control action.", 7.32, 5.28, 5.32, 0.38, {
    fontSize: 7.8, color: C.ink, bold: true, valign: "top",
  });

  const reasons = [
    ["IEC 61511 / SIS", "Safety-instrumented functions are not arbitrated by a cloud model.", C.rust],
    ["IEC 62443 zones", "The conduit is outbound-only; no inbound session reaches the cell.", C.amber],
    ["EU AI Act", "Actuation would assume high-risk duties we cannot yet evidence.", C.teal],
    ["Reversibility", "Rejected advice costs a click; a wrong setpoint can cost €8M.", C.graphite],
  ];
  reasons.forEach((r, i) => {
    const x = 0.5 + i * 3.1225;
    card(slide, x, 5.92, 2.9625, 0.74, { fill: C.white, border: C.mist, bar: r[2] });
    tx(slide, r[0].toUpperCase(), x + 0.2, 6.045, 2.6, 0.11, { fontSize: 8, color: r[2], bold: true, charSpacing: 0.7 });
    tx(slide, r[1], x + 0.2, 6.27, 2.56, 0.28, { fontSize: 7, color: C.muted, valign: "top" });
  });

  finish(slide, 27,
    "This is the question I want. Not writing to the furnace is a decision, not a gap. Setpoints, interlocks, and control logic live at Purdue levels zero to two, under IEC 61511 safety-instrumented functions and vendor certification, and our conduit across that boundary is outbound-only by design.\nBut the platform is not a read-only dashboard. It writes decisions: an approved energy dispatch, a maintenance work order, a published procedure, and an append-only record of who decided what against which model version. That is a decision system of record.\nActuation is a Phase 2 conversation and it starts with guarded write-back to CMMS and MES under human approval and thresholds, never a direct control action. Advice that is wrong costs a rejection; a setpoint that is wrong can cost an eight-million-euro event.",
    "Source cue | FAQ H — faq.md Q39b  •  solution-requirements.md O1, C-04, AI-05, §18 phasing  •  solution-architecture.md §1.1, ADR-007/008",
  );
}

// 28 — backup: ingestion service choice
{
  const slide = newSlide(28, "Architecture decision ADR-016", "Why not Azure IoT Hub — or IoT Operations?", "", { backup: true, dark: true, texture: true });
  badge(slide, 0.5, 1.3, "Ingress defense", "guardrail", 1.5);
  tx(slide, "The ingress can only receive. Choosing a device-management service would buy us the inbound control plane we promised not to build.", 2.13, 1.335, 8.6, 0.18, {
    fontSize: 8.4, color: C.steel, bold: true,
  });

  label(slide, 0.5, 1.78, "Three candidates, one verdict each", C.steel, 4.2);
  const candidates = [
    ["AZURE EVENT HUBS", "CHOSEN", C.teal,
      "Outbound-only buffer, one hub per plant. Local auth disabled, private endpoint, and each mi-ns-otgw-<plant> identity scoped to its own hub — not the namespace. The relay then publishes to the Fabric Eventstream Custom Endpoint with a workload identity.",
      "1 TU  ·  disableLocalAuth: true  ·  private endpoint  ·  per-hub Data Sender"],
    ["AZURE IOT HUB", "REJECTED", C.rust,
      "Its differentiators over Event Hubs are all cloud-to-device: provisioning (DPS), twins, direct methods, jobs. Every one of them is an inbound path into the plant, and device authentication is per-device key or certificate.",
      "Would add: DPS  ·  device twins  ·  direct methods  ·  jobs  —  all cloud-to-device"],
    ["AZURE IOT OPERATIONS", "DEFERRED", C.amber,
      "The 2026 strategic industrial stack: Arc-enabled MQTT broker, OPC UA connector, data flows native to Fabric. The right answer the day the OT edge, gateway lifecycle, or per-sensor cloud identity enters scope — not before.",
      "Cost of entry: an Arc-enabled Kubernetes footprint inside every plant"],
  ];
  candidates.forEach((c, i) => {
    const y = 1.99 + i * 1.3;
    card(slide, 0.5, y, 6.15, 1.18, { dark: true, fill: C.coal, border: c[2], bar: c[2], lineWidth: 0.9 });
    tx(slide, c[0], 0.78, y + 0.17, 3.5, 0.14, { fontSize: 9.4, color: C.white, bold: true, charSpacing: 0.6 });
    roundRect(slide, 5.32, y + 0.14, 1.11, 0.24, c[2], c[2], { lineWidth: 0.4 });
    tx(slide, c[1], 5.37, y + 0.225, 1.01, 0.09, { fontSize: 6.4, color: C.carbon, bold: true, align: "center" });
    tx(slide, c[3], 0.78, y + 0.46, 5.6, 0.5, { fontSize: 7.6, color: C.steel, valign: "top" });
    line(slide, 0.78, y + 0.94, 5.6, 0, C.graphite, 0.6);
    tx(slide, c[4], 0.78, y + 0.985, 5.6, 0.1, { fontSize: 6.6, color: C.mist, fontFace: F.mono });
  });

  label(slide, 7.05, 1.78, "Why IoT Hub loses on our own guardrails", C.steel, 5.4);
  const reasons = [
    ["01", "IT SELLS THE CONTROL PLANE WE BANNED", "O1 / C-04 / AI-05 forbid a write path to OT. We would acquire the capability, disable it, then keep proving it stays disabled.", C.rust],
    ["02", "IT WEAKENS THE NO-KEY POSTURE", "Event Hubs runs disableLocalAuth: true with Entra RBAC. IoT Hub device auth is SAS or X.509, and Fabric's IoT Hub source is key-based — the very thing ADR-005 avoids.", C.amber],
    ["03", "THE SENDERS ARE FOUR GATEWAYS", "Not a device fleet. Per-device identity already rides the envelope (source_id, asset_id) and the Device Operations registry — 17 devices, 91 sensors.", C.teal],
    ["04", "NO NEW CAPABILITY, A NEW BILL", "A second ingestion service on a deliberately minimal footprint: one throughput unit, small Fabric capacity, nightly pause.", C.green],
  ];
  reasons.forEach((r, i) => {
    const y = 1.99 + i * 0.99;
    card(slide, 7.05, y, 5.78, 0.87, { dark: true, fill: C.coal, border: C.graphite, bar: r[3], lineWidth: 0.7 });
    circle(slide, 7.28, y + 0.19, 0.28, r[3], r[3]);
    tx(slide, r[0], 7.28, y + 0.288, 0.28, 0.09, { fontSize: 7, color: C.carbon, bold: true, align: "center" });
    tx(slide, r[1], 7.72, y + 0.16, 4.9, 0.13, { fontSize: 8.2, color: C.white, bold: true, charSpacing: 0.4 });
    tx(slide, r[2], 7.72, y + 0.44, 4.9, 0.36, { fontSize: 7.1, color: C.steel, valign: "top" });
  });

  card(slide, 0.5, 5.95, 12.33, 0.7, { dark: true, fill: C.oxide, border: C.rust, bar: C.amber, lineWidth: 0.9 });
  tx(slide, "REVISIT WHEN", 0.78, 6.09, 1.5, 0.12, { fontSize: 7.6, color: C.amber, bold: true, charSpacing: 0.9 });
  tx(slide, "a business requirement demands cloud-initiated action on plant equipment, or gateways can no longer aggregate upstream devices. The migration target is then IoT Operations, not IoT Hub — and closed-loop control of machinery changes the EU AI Act risk classification, so it reopens the conformity assessment.", 2.14, 6.06, 10.45, 0.44, {
    fontSize: 7.7, color: C.mist, bold: true, valign: "top",
  });

  finish(slide, 28,
    "If the panel knows industrial Azure, this is the first question they ask: these are furnaces, so why is there no IoT Hub?\nBecause what IoT Hub adds over Event Hubs is a cloud-to-device control plane — device provisioning, twins, direct methods, jobs. Every one of those is an inbound path into the plant. Our advisory boundary is an acceptance criterion, not a gap, so we would be buying a capability we must never use, disabling it, and then carrying the burden of proving it stays disabled in every threat model review. Event Hubs simply cannot do it.\nIt would also cost us the no-standing-secret property. Our namespace runs with local authentication disabled, behind a private endpoint, and each plant gateway identity can write to exactly one hub. IoT Hub authenticates devices with per-device keys or certificates, and Fabric's IoT Hub source connector is a shared-access-policy connection — the exact pattern ADR-005 exists to eliminate.\nAnd the shape is wrong: we have four plant gateways, not a fleet of thousands. Device identity already lives in the event envelope and in Device Operations.\nThe honest forward-looking answer is that if the OT edge itself ever comes into scope, the strategic path in 2026 is Azure IoT Operations — Arc-enabled, MQTT broker, OPC UA connector, native to Fabric. Not IoT Hub. Moving to IoT Hub today would be adopting the older device-centric service to solve a problem we do not have.",
    "Source cue | FAQ C — faq.md Q14b  •  solution-architecture.md ADR-016, ADR-005, §4.1  •  infra/bicep/modules/eventhubs.bicep",
    true,
  );
}

async function build() {
  [texture, hero, thermalMap].forEach(ensureAsset);
  if (SLIDE_LIMIT > 0 && SLIDE_LIMIT < pptx._slides.length) {
    pptx._slides.splice(SLIDE_LIMIT);
  }
  fs.mkdirSync(path.dirname(OUTPUT), { recursive: true });
  await pptx.writeFile({ fileName: OUTPUT });
  console.log(`Wrote ${OUTPUT}`);
  console.log(`Slides: ${pptx._slides.length}`);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
