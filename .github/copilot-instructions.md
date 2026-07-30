# Copilot instructions

## Package feeds (mandatory security policy)

Microsoft-managed devices block direct access to public package registries. Never generate commands, config, Dockerfiles, CI workflows, or docs that point at these endpoints:

- `pypi.org/simple`
- `files.pythonhosted.org`
- `api.nuget.org`
- `nuget.org/api/v2`

Always use the Microsoft-protected feeds backed by Central Feed Services (CFS):

| Manager | Feed URL |
| --- | --- |
| pip / PyPI | `https://packagefeedproxy.microsoft.io/pypi/simple` |
| NuGet | `https://packagefeedproxy.microsoft.io/nuget/v3/index.json` |

Rules:

- Do not add `--index-url`, `--extra-index-url`, or `<add key="nuget.org" .../>` entries that reference public registries.
- Reuse the existing repo configuration instead of inventing new ones: [NuGet.Config](../NuGet.Config), [pip.conf](../pip.conf), [.npmrc](../.npmrc).
- New Python services must ship a `pip.conf` (or set `PIP_INDEX_URL`) pointing at the protected feed; new .NET projects inherit the root `NuGet.Config` with `<clear />` and package source mapping.
- Container images and CI jobs must copy or set the same feed configuration before restoring packages.
- If a package is unavailable on the protected feed, stop and ask the user to use the approved CFS exception process. Do not fall back to the public registry.

Reference: [docs/tech/security_requirement.md](../docs/tech/security_requirement.md)
