# Toolchain resolution policy and research

> **Research date:** 2026-07-25  
> **Status:** Supporting research. The [solution architecture](../architecture/solution-architecture.md) is authoritative for the chosen shape; this document records how versions are selected, not version promises.

## Decision

NovaSteel uses a **Blazor WebAssembly C# shell**, a **React/TypeScript analytics microfrontend** using Material UI and D3, and **Python/FastAPI** domain services. This reconciles the C# presentation requirement with the MUI/D3 requirement while keeping one authoritative Python API and domain-compute layer.

| Layer | Chosen responsibility | Version-resolution rule |
|---|---|---|
| C# shell | Blazor WASM, MSAL, navigation, locale/theme, typed host bridge | Select a supported .NET LTS channel at bootstrap; record the exact SDK in `global.json` and lockfile/provenance. |
| Analytics MFE | React/TypeScript, MUI, D3, virtualized tables, optional internal Power BI embed | Select mutually compatible supported releases from the approved protected feed; commit exact lockfile versions only after compatibility tests. |
| Backend | Python/FastAPI, validation, SSE, query adapters, audit and capacity mediation | Select a supported CPython release and compatible package set; pin the resolved graph with hashes/lockfile. |
| Workers and simulator | Python deterministic scoring, optimization, simulation, and validators | Resolve from the same approved Python feed and capture generator/dependency provenance. |
| Azure/Fabric clients | Service-specific SDKs and REST clients | Use the minimum stable client API that supports the required Entra-ID flow; revalidate service support before release. |

No exact language, framework, package, action, model, or SDK version in this research is an architecture commitment. The sole deliberate API pin is the Fabric capacity ARM version stated in the [architecture](../architecture/solution-architecture.md); it is rechecked against the official REST reference before a major release.

## Compatibility and provenance gate

Before a version reaches a demo, test, or production environment:

1. Resolve dependencies only through the organization-approved protected feeds.
2. Review the lockfile diff and generate an SBOM.
3. Run vulnerability, license, unit, contract, integration, and relevant browser/accessibility tests.
4. Record SDK/runtime/package versions, hashes, test result, and rollback version in release provenance.
5. Reject preview packages and preview service features from the demo critical path.

The exact protected-feed configuration and CI enforcement live in the [implementation guide](../implementation/implementation-guide.md) and [security governance](../security/security-governance-and-threat-model.md). No public registry is an approved source or fallback.

## Frontend boundary

The shell and MFE are one demonstration release unit to prevent host/bridge skew:

- The **Blazor WASM shell** owns Entra sign-in, routing, global chrome, theme, locale, and token brokering.
- The **React MFE** owns MUI components, D3 charts, accessible virtualized tables, and the optional internal Power BI surface.
- The MFE receives typed context only; it never receives a workload credential or becomes an authorization boundary.
- The **FastAPI BFF** owns all business/data APIs and server-side authorization. A second C# BFF is out of scope.

## Sources to recheck at bootstrap

| Topic | Official source |
|---|---|
| .NET support policy | [Microsoft .NET support policy](https://dotnet.microsoft.com/platform/support/policy/dotnet-core) |
| Python release lifecycle | [Python developer guide: status of Python versions](https://devguide.python.org/versions/) |
| Azure SDK support and releases | [Azure SDK releases](https://azure.github.io/azure-sdk/releases/latest/index.html) |
| Fabric capacity API | [Fabric capacity REST API](https://learn.microsoft.com/rest/api/microsoftfabric/fabric-capacities/resume) |
| Secure dependency policy | [Security governance](../security/security-governance-and-threat-model.md) |

The build-time task list, GitHub Actions/OIDC requirements, and Copilot task workflow are authoritative in the [implementation guide](../implementation/implementation-guide.md).
