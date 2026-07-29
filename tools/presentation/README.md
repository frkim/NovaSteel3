# NovaSteel oral-defense deck source

This directory contains the editable generation source and generated visual assets for
`docs\presentation\NovaSteel-Oral-Defense.pptx`.

```powershell
Set-Location tools\presentation
$env:NPM_CONFIG_REGISTRY = "https://<approved-npm-protected-feed>"
npm ci --ignore-scripts
npm run assets
npm run build
```

The npm registry is the configured Microsoft-protected package feed. The build creates
the 20 timed main slides (a 35-minute talk, handing over to a 10-minute demo) plus eight
FAQ/validation backup slides. `build-deck.js` uses
PptxGenJS native shapes for diagrams and speaker notes where the library supports them.
