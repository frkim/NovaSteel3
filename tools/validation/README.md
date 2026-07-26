# Repository validation

Run all locally feasible checks with:

```powershell
pwsh .\tools\validation\Validate-Repository.ps1
```

The command runs schema, simulator, backend/integration, knowledge, React,
Blazor, Bicep, Fabric, presentation, security, and SBOM checks. It writes logs,
reports, and `evidence-manifest.json` below `artifacts\validation`.

`-RestoreDependencies` performs `npm ci --ignore-scripts` only when
`NPM_CONFIG_REGISTRY` names an approved non-public HTTPS feed. Python and NuGet
restores use the repository's protected feed configuration. The script performs
no Azure login, what-if, or deployment.
