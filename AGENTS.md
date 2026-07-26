# Agent instructions

## Package feeds (mandatory security policy)

Public PyPI and NuGet registries are blocked on Microsoft-managed devices. Never use or suggest `pypi.org/simple`, `files.pythonhosted.org`, `api.nuget.org`, or `nuget.org/api/v2`.

Always restore packages through the Microsoft-protected feeds:

- pip / PyPI: `https://packagefeedproxy.microsoft.io/pypi/simple`
- NuGet: `https://packagefeedproxy.microsoft.io/nuget/v3/index.json`

Reuse the existing [NuGet.Config](NuGet.Config), [pip.conf](pip.conf), and [.npmrc](.npmrc); do not override them with public sources in scripts, Dockerfiles, or CI. If a package is missing from the protected feed, stop and ask for the approved exception process rather than falling back to a public registry.

Full details: [.github/copilot-instructions.md](.github/copilot-instructions.md) and [docs/tech/security_requirement.md](docs/tech/security_requirement.md)
