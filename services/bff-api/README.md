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

## Adapters and configuration

Persistence and AI adapters are chosen at startup by a factory, so the same
code path serves both the offline demo and the deployed environment:

| Env var | Effect when set | Default when unset |
|---|---|---|
| `NOVASTEEL_TABLE_ENDPOINT` + `NOVASTEEL_STORAGE_ACCOUNT_NAME` | Audit hash-chain and idempotency records persist in Azure Table Storage via `DefaultAzureCredential` | In-memory stores, reset on restart |
| `FOUNDRY_ENDPOINT` (+ `KNOWLEDGE_AGENT_MODE=azure`) | Knowledge extraction calls the Foundry chat deployment (`gpt-5.4-mini`) | Local deterministic fixture agent |
| `FOUNDRY_PROJECT_ENDPOINT` (+ `FOUNDRY_AGENT_SERVICE_MODE=azure`) | The procedure agent is hosted in Foundry Agent Service and answers via a Foundry IQ knowledge base | Local in-process agent over the approved corpus |
| `AI_SEARCH_ENDPOINT` | Approved procedures are indexed into and retrieved from Azure AI Search | In-memory procedure store seeded from fixtures |
| `ONLINE_SEARCH_MODE=web_iq\|web_search` | Copilot chat "Online Search" grounds on live web results | `offline` — the curated corpus only |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | OpenTelemetry traces and business KPI metrics export to Azure Monitor | Instrumentation is a silent no-op |
| `NOVASTEEL_LOG_FORMAT=json` | Structured JSON logs to stdout with `correlation_id` as a field | Human-readable console output |

Instrumentation never blocks startup: a missing, unimportable or misconfigured
exporter degrades to a no-op rather than raising. The SHA-256 audit hash chain
is preserved identically by both the local and Azure Table adapters.
