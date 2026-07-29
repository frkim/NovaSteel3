// Copies the brand assets and UI screenshots the deck references from their
// canonical locations in the repository into presentation/images/.
//
// The images are deliberately not committed twice: docs/presentation/assets and
// apps/portal-shell/wwwroot/brand remain the single source of truth, and
// presentation/images/ is a build output (see presentation/.gitignore).
//
// Usage: node scripts/sync-images.mjs

import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const presentationDir = resolve(here, "..");
const repoRoot = resolve(presentationDir, "..");
const targetDir = join(presentationDir, "images");

const brandDir = join(repoRoot, "apps", "portal-shell", "wwwroot", "brand");
const generatedDir = join(repoRoot, "tools", "presentation", "assets");
const screenshotDir = join(
  repoRoot,
  "docs",
  "presentation",
  "assets",
  "app-guide",
  "screenshots",
);

/** @type {Array<[string, string]>} source path -> file name inside images/ */
const assets = [
  [join(brandDir, "novasteel-logo-full.png"), "novasteel-logo-full.png"],
  [join(brandDir, "novasteel-mark.png"), "novasteel-mark.png"],
  [join(brandDir, "axelormetal-wordmark.png"), "axelormetal-wordmark.png"],
  [join(generatedDir, "steelworks-hero.png"), "steelworks-hero.png"],
  [join(generatedDir, "thermal-map.png"), "thermal-map.png"],
  ...[
    "command-center-overview.png",
    "energy-optimization-spot-price-schedule.png",
    "furnace-health-lining-forecast.png",
    "furnace-health-thermal-explorer.png",
    "quality-spc.png",
    "knowledge-hub-capture-status.png",
    "sustainability-emissions-ledger.png",
    "executive-overview.png",
    "device-operations-fleet.png",
  ].map((name) => [join(screenshotDir, name), name]),
];

const missing = assets.filter(([source]) => !existsSync(source));
if (missing.length > 0) {
  console.error("sync-images: missing source assets:");
  for (const [source] of missing) {
    console.error(`  - ${source}`);
  }
  process.exit(1);
}

if (existsSync(targetDir)) {
  for (const entry of readdirSync(targetDir)) {
    rmSync(join(targetDir, entry), { recursive: true, force: true });
  }
} else {
  mkdirSync(targetDir, { recursive: true });
}

for (const [source, name] of assets) {
  copyFileSync(source, join(targetDir, name));
}

console.log(`sync-images: copied ${assets.length} assets into ${targetDir}`);
