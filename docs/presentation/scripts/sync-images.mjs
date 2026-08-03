// Copies the brand assets and UI screenshots the deck references from their
// canonical locations in the repository into docs/presentation/images/.
//
// The images are deliberately not committed twice: docs/presentation/assets,
// docs/images/logo and apps/portal-shell/wwwroot/brand remain the single source of
// truth, and docs/presentation/images/ is a build output (see
// docs/presentation/.gitignore).
//
// Usage: node scripts/sync-images.mjs

import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const presentationDir = resolve(here, "..");
const repoRoot = resolve(presentationDir, "..", "..");
const targetDir = join(presentationDir, "images");

const brandDir = join(repoRoot, "apps", "portal-shell", "wwwroot", "brand");
const logoDir = join(repoRoot, "docs", "images", "logo");
const docsImageDir = join(repoRoot, "docs", "images");
const generatedDir = join(repoRoot, "tools", "presentation", "assets");
const diagramDir = join(repoRoot, "docs", "presentation", "assets", "diagrams");
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
  [join(diagramDir, "steel-process-routes.webp"), "steel-process-routes.webp"],
  [join(generatedDir, "steelworks-hero.png"), "steelworks-hero.png"],
  [join(generatedDir, "thermal-map.png"), "thermal-map.png"],
  [join(docsImageDir, "Fabric Architecture Diagram.png"), "fabric-architecture-diagram.png"],
  [join(docsImageDir, "Fabric RTI Diagram.png"), "fabric-rti-diagram.png"],
  ...[
    "adaptive-cloud-iot-operations.png",
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

/**
 * Title-slide logos, resolved from the first candidate that exists. The preferred
 * candidate is always the file under docs/images/logo/, so dropping the exact asset
 * there overrides the fallback without touching this script. A logo whose candidates
 * are all absent is simply not copied: the title slide drops that slot rather than
 * rendering a broken image.
 *
 * @type {Array<[string, string[]]>} file name inside images/ -> candidate sources
 */
const logos = [
  ["novasteel-logo.png", [join(logoDir, "NovaSteel Logo.png")]],
  ["microsoft-logo.png", [join(logoDir, "microsoft_logo.png")]],
];

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

let copiedLogos = 0;
for (const [name, candidates] of logos) {
  const source = candidates.find((candidate) => existsSync(candidate));
  if (source === undefined) {
    console.warn(`sync-images: no source for ${name}; the title slide will omit that logo`);
    continue;
  }
  copyFileSync(source, join(targetDir, name));
  copiedLogos += 1;
}

console.log(
  `sync-images: copied ${assets.length + copiedLogos} assets into ${targetDir}`,
);
