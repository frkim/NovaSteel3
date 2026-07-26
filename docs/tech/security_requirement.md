# New Protection for Software Package Downloads

**CISO Organization**

Microsoft-managed devices block direct access to public **PyPI** and **NuGet** registries to reduce software supply chain risk. Package downloads must go through Microsoft-protected feeds backed by **Central Feed Services (CFS)**.

## Blocked Endpoints

Prohibition list only — never use as a configuration template:

- `pypi.org/simple`
- `files.pythonhosted.org`
- `api.nuget.org`
- `nuget.org/api/v2`

## Approved Package Feeds

| Manager | Feed URL |
| --- | --- |
| PyPI | `packagefeedproxy.microsoft.io/pypi/simple` |
| NuGet | `packagefeedproxy.microsoft.io/nuget/v3/index.json` |

## Impact

- Projects already using approved Microsoft feeds or dedicated **Azure Artifacts** feeds continue to work.
- Package managers with no explicit configuration are routed to Microsoft-protected feeds by policy.
- If a tool cannot reach PyPI or NuGet, configure it to use the approved feed above; see CFS guidance on EngHub for exception scenarios.


