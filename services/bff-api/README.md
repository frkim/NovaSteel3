# NovaSteel BFF API

The BFF implements the v1 browser-facing contract: demo/Entra authorization
boundaries, plant scoping, command-center KPIs, telemetry, furnace RUL,
energy recommendations, quality/genealogy/what-if, sustainability, knowledge,
append-only audit, SSE/poll alerts, work orders, and capacity lifecycle.
It is advisory-only and has no OT/control write path.

## Local demo mode

```powershell
$env:PIP_CONFIG_FILE = "$PWD\pip.conf"
$env:PIP_INDEX_URL = "https://packagefeedproxy.microsoft.io/pypi/simple"
.\services\bff-api\.venv\Scripts\python.exe -m pip install --index-url https://packagefeedproxy.microsoft.io/pypi/simple -r .\services\bff-api\requirements.txt
$env:DEMO_MODE = "local"
$env:PYTHONPATH = "$PWD\services\bff-api\src"
.\services\bff-api\.venv\Scripts\python.exe -m uvicorn bff_api.main:app --host 127.0.0.1 --port 8080
```

`DEMO_MODE=local` refuses a non-`NS-DEMO-*` namespace. Configure CORS with
`BFF_CORS_ORIGINS` as a comma- or semicolon-separated origin list. The default
already allow-lists the portal shell dev origins from its `launchSettings.json`
(`http://localhost:5266`, `https://localhost:7075`) plus the Vite dev server
(`http://localhost:5173`), so the documented `dotnet run` demo works without
extra configuration. It loads the generated `fixtures\demo-full` simulator
dataset and falls back to a minimal synthetic fixture only if that data is
unavailable.

Demo requests must explicitly provide a persona/plant stub; for example:

```powershell
$headers = @{
  "X-Demo-User" = "demo-energy-manager"
  "X-Demo-Roles" = "EnergyPlanner.Approve,MaintenanceEngineer.Read"
  "X-Demo-Plants" = "NS-DEMO-LUX-01"
}
Invoke-RestMethod http://127.0.0.1:8080/v1/me -Headers $headers
```

Outside local mode, the BFF fails closed until `BFF_JWT_VALIDATOR_MODULE`
points to an organization-provided JWKS/signature-validating
`module:function` adapter. That adapter must validate Entra signature, issuer,
audience, expiry, and not-before before returning claims. The ARM capacity
adapter is likewise an interface boundary; local capacity actions are always
simulated.
