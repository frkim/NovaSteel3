// Verifies the artifacts produced by `npm run build` before they are published.
//
// Usage: node scripts/verify-build.mjs

import AdmZip from "adm-zip";
import { readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const distDir = resolve(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const slidesSource = resolve(distDir, "..", "slides.md");

const expectedSlides = readFileSync(slidesSource, "utf8")
  .split(/^---\s*$/m)
  .slice(2).length;

const failures = [];

function check(condition, message) {
  if (!condition) failures.push(message);
}

function size(name) {
  try {
    return statSync(join(distDir, name)).size;
  } catch {
    return 0;
  }
}

for (const pdf of ["NovaSteel-Oral-Defense.pdf", "NovaSteel-Oral-Defense-notes.pdf"]) {
  const bytes = size(pdf);
  check(bytes > 0, `${pdf} is missing or empty`);
  if (bytes > 0) {
    check(
      readFileSync(join(distDir, pdf)).subarray(0, 5).toString("latin1") === "%PDF-",
      `${pdf} is not a PDF document`,
    );
  }
}

const html = size("index.html") > 0 ? readFileSync(join(distDir, "index.html"), "utf8") : "";
check(html.length > 0, "index.html is missing or empty");
const htmlSlides = (html.match(/<section /g) || []).length;
check(
  htmlSlides === expectedSlides,
  `index.html renders ${htmlSlides} slides, expected ${expectedSlides}`,
);

const pptxPath = join(distDir, "NovaSteel-Oral-Defense.pptx");
check(size("NovaSteel-Oral-Defense.pptx") > 0, "NovaSteel-Oral-Defense.pptx is missing or empty");
if (size("NovaSteel-Oral-Defense.pptx") > 0) {
  const entries = new AdmZip(pptxPath).getEntries().map((entry) => entry.entryName);
  const pptxSlides = entries.filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name)).length;
  const noteSlides = entries.filter((name) =>
    /^ppt\/notesSlides\/notesSlide\d+\.xml$/.test(name),
  ).length;
  check(
    pptxSlides === expectedSlides,
    `PPTX contains ${pptxSlides} slides, expected ${expectedSlides}`,
  );
  check(noteSlides === expectedSlides, `PPTX carries speaker notes on ${noteSlides} slides`);
}

if (failures.length > 0) {
  console.error("verify-build: FAILED");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

console.log(`verify-build: ok — ${expectedSlides} slides in HTML, PDF, speaker-note PDF and PPTX`);
