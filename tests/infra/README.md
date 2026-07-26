# tests/infra — infrastructure-focused validation

Pytest suite that statically validates `infra/` (Bicep templates, `.bicepparam` files, custom
Azure Policy definitions, and deployment scripts) without deploying anything or requiring a
Fabric/Foundry tenant. Network-touching validation (`az deployment sub validate`/`what-if`)
belongs to CI (`cd-infra.yml`) using a live OIDC session — see `infra/scripts/validate.ps1` and
`infra/README.md`.

## Running

```powershell
cd tests/infra
pip install -r requirements-test.txt
pytest
```

Tests that need the `az`/`bicep` CLI or `pwsh`/`powershell` skip (not fail) automatically when
the tool is unavailable, so this suite also runs in a minimal Python-only environment — though
`az bicep build`/`build-params` coverage is the most valuable part and should be run wherever
possible (Azure CLI 2.76+ with the Bicep extension was used to author and verify this suite).

## What is covered

| File | Covers |
|---|---|
| `test_bicep_build.py` | Every `.bicep` file compiles with zero errors (`az bicep build`); the documented module inventory exists. |
| `test_bicep_params.py` | Every `.bicepparam` file compiles against `main.bicep` (`az bicep build-params`); exactly one file per environment. |
| `test_naming_conventions.py` | Resource-group/Fabric-capacity/Event-Hubs naming matches `deployment-topology.md` §3.2; the `location` parameter defaults to Sweden Central with West Europe as the only explicit contingency; no `Microsoft.Fabric/<item>` type other than `capacities` is ever declared; no shared-key/SAS/connection-string retrieval calls exist; public network access is disabled by default on every data-plane PaaS module; the 01:00 capacity lifecycle Logic App is never deployed for `prod`; the Luxembourg time zone mapping is correct. |
| `test_policy_definitions.py` | Every custom policy JSON file is well-formed, cites its source requirement, and is actually wired into `policy-assignments.bicep`. |
| `test_parameters_completeness.py` | Cross-environment consistency: `expiryDate` mandatory for demo, exactly one environment owns the subscription-wide guardrail singleton, prod has a stricter posture, the Foundry Agent Service gate ships disabled everywhere, budgets have contacts. |
| `test_scripts.py` | Every deployment script exists and parses cleanly; none embeds a static Azure credential; `deploy.ps1` refuses to run with `AZURE_CLIENT_SECRET`/`AZURE_CREDENTIALS` set; the app-registration script defaults to a dry run. |

## Not covered here (by design)

- Live `az deployment sub validate`/`what-if`/`create` — requires a real subscription and Azure/
  OIDC session; run via `infra/scripts/validate.ps1`/`what-if.ps1`/`deploy.ps1` in CI or by a
  developer with `az login`.
- Fabric SaaS-item (workspace/Eventstream/Lakehouse/etc.) provisioning and its tests — owned by
  the `fabric/` workstream, not `infra/`.
- Application-level tests (contract/integration/e2e/simulator) — see `tests/contract`,
  `tests/integration`, `tests/simulator`, `tests/e2e` per `solution-architecture.md` §11.
