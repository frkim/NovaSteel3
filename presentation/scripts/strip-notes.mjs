// Writes slides.pages.md: a copy of slides.md without speaker notes, used for
// the public GitHub Pages deck so presenter narration is never published.
//
// Marp directives are HTML comments too, so only comments whose first
// non-whitespace character is not an underscore are removed.
//
// Usage: node scripts/strip-notes.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const presentationDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = join(presentationDir, "slides.md");
const target = join(presentationDir, "slides.pages.md");

const stripped = readFileSync(source, "utf8").replace(/<!--(?!\s*_)[\s\S]*?-->/g, "");

writeFileSync(target, stripped, "utf8");
console.log(`strip-notes: wrote ${target} without speaker notes`);
