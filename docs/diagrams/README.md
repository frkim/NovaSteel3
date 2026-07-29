# NovaSteel editable diagrams

Open these source files in the Microsoft internal Excalidraw instance at <https://aka.ms/excalidraw>. Each diagram uses a clear grid, Fluent-aligned colors, transparent grouping containers, filled leaf nodes, and black text.

- **`end-to-end-architecture.excalidraw`** — End-to-end data, AI, and experience architecture. It traces deterministic simulators and the read-only OT edge through Event Hubs and the Fabric Eventstream/RTI/Eventhouse/OneLake/Lakehouse core, then into semantic reporting, Python APIs and workers, Foundry Agent Service/Speech STT, and the Blazor plus React/MUI/D3 experience. The bottom band shows identity, security, observability, audit, and fallback controls.
- **`deployment-topology.excalidraw`** — EU deployment and managed-service placement. It shows the four-country site boundary, Sweden Central hub/spokes, Fabric SaaS plane, managed Azure services, isolated environments, and the explicitly tested—not automatic—West Europe recovery posture.
- **`demo-flow.excalidraw`** — The timed 10-minute persona journey from Plant Manager and Fabric Core through energy, reliability, quality, operator knowledge, sustainability/executive evidence, and final recap. Dashed branches and the fallback ladder show when to use local replay, cached results, recordings, or the static proof pack.

- **`business-value-chain.excalidraw`** — The executive business-hook diagram for Slides 1–4. It traces the value chain from four EU production sites (Luxembourg HQ, Germany, Belgium, Spain) through Event Hubs ingestion, the governed Fabric core (RTI, OneLake, Direct Lake, Power BI), four AI capabilities (RUL, Energy MILP, Quality, Knowledge), into human decision-makers and audited outcomes, with a guardrails bar showing EU residency, identity, audit, and RAI governance.

The `.excalidraw` JSON files are the editable masters; keep them alongside any exported PNG or SVG derivatives.
