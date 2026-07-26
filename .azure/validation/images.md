# NovaSteel v3 — Image build validation proof

> **Scope:** `azure-validate-images` (application image packaging).
> **Result:** ✅ **PASS** — portal and BFF images rebuilt, all smoke tests and
> additional image checks green. No push/deploy performed.
> **Validated (UTC):** 2026-07-25T07:2x
> **Host:** Docker Engine 29.6.2, Buildx v0.35.0-desktop.2, platform `linux/x86_64`.

---

## 1. Images produced (immutable tags + digests)

Rebuilt from the current Dockerfiles with `.azure\scripts\build-images.ps1`
(BuildKit named build contexts; `--load`, no registry, no push).

| Image | Immutable tag | Content-addressable digest (image ID) | Size |
|---|---|---|---|
| BFF | `novasteelv3/bff:1.0.0-20260725072746-nogit` | `sha256:1db63dbc74c4406727310201d59b6cf7c9c2a7af0fcb9afe75fd60a1245e8d33` | 247 MB |
| Portal | `novasteelv3/portal:1.0.0-20260725072746-nogit` | `sha256:fcf3563710dd47659e60a6a073ffc4fb58e9eb43b8b50e8b5a6085ebab7ac1eb` | 122 MB |

Convenience aliases `novasteelv3/bff:local` and `novasteelv3/portal:local` point
at the same digests (used by the smoke tests).

**Immutability:** the deploy tag embeds a UTC build stamp
(`1.0.0-<yyyyMMddHHmmss>-<git-sha>`), so a new build never clobbers a prior tag
(e.g. an earlier `...-20260725071500-...` tag coexists). The `-nogit` component is
expected here because this checkout has no `.git` directory
(`git rev-parse HEAD` → `fatal: not a git repository`); the timestamp still
guarantees a unique, non-overwriting tag, and each image is additionally
addressable by its `sha256` digest above. **No `:latest`/mutable tag is used for
deploy.**

Build log: `artifacts/validation/build-images.log`.

```powershell
pwsh .\.azure\scripts\build-images.ps1
# ==> both targets built; final table:
# bff     novasteelv3/bff:1.0.0-20260725072746-nogit     sha256:1db63dbc...
# portal  novasteelv3/portal:1.0.0-20260725072746-nogit  sha256:fcf35637...
```

---

## 2. Protected feed / security scan (Dockerfiles + configs)

Both repository scanners cover the Dockerfiles (`is_executable_config` treats
`dockerfile*` as scannable) and the feed configs, and both **PASS**.

| Check | Command | Result |
|---|---|---|
| Protected-feed policy | `python tools/validation/verify_protected_feeds.py --root . --json artifacts/validation/protected-feeds.json` | **PASS** — 378 files checked, 0 violations (no `pypi.org/simple`, `files.pythonhosted.org`, `api.nuget.org`, `nuget.org/api/v2`) |
| Repository security gates | `python tools/validation/security_scan.py --root . --json artifacts/validation/security.json` | **PASS** — 0 findings (protected pip.conf + cleared NuGet.Config, pinned requirements, no secret literals) |
| Dockerfile feed grep | `Select-String services\bff-api\Dockerfile, apps\portal-shell\Dockerfile -Pattern <public feeds>` | **Clean** — no public PyPI/NuGet/npm endpoints in either Dockerfile |

Reports: `artifacts/validation/protected-feeds.json`, `artifacts/validation/security.json`.

**Baked into the BFF runtime image** (verified inside the container):

```text
/etc/pip.conf:
  [global]
  index-url = https://packagefeedproxy.microsoft.io/pypi/simple
  disable-pip-version-check = true
  extra-index-url? -> NONE (good)      # no public fallback
PIP_INDEX_URL env -> https://packagefeedproxy.microsoft.io/pypi/simple
```

NuGet restore (portal build) uses `NuGet.Config` with `<clear/>` + the single
protected feed `packagefeedproxy.microsoft.io/nuget/v3/index.json`; the
`dotnet restore`/`publish` succeeded with no public `nuget.org` fallback.

> **Note (in scope per task = *Python/NuGet* only):** the portal MFE stage runs
> `npm ci` against the public npm registry. That is intentional and outside the
> protected-feed requirement, which the task scopes to Python and NuGet.

---

## 3. Smoke tests — `.azure\scripts\test-images.ps1`

Command: `pwsh .\.azure\scripts\test-images.ps1` → **13 passed, 0 failed.**
Log: `artifacts/validation/test-images.log`.

| # | Assertion | Contract verified | Result |
|---|---|---|---|
| 1 | `/health/live` 200 + `status:ok` | BFF liveness probe (8080) | ✅ |
| 2 | `/health/ready` 200 + `status:ok` | BFF readiness probe (8080) | ✅ |
| 3 | `/v1/meta demoMode=true` | Deterministic demo mode | ✅ |
| 4 | `/v1/meta environment=demo` | Demo environment | ✅ |
| 5 | CORS allows configured portal origin | `Access-Control-Allow-Origin` == env origin | ✅ |
| 6 | CORS rejects unlisted origin | no ACAO header for `evil.example.com` | ✅ |
| 7 | Deterministic fixture `simulator-fixture:demo-full` loaded | Repeatable demo data | ✅ |
| 8 | `/` 200 serves SPA host (`<div id="app"`) | Portal probe path (8080) | ✅ |
| 9 | `/healthz` 200 | Portal local health endpoint | ✅ |
| 10 | SPA fallback for deep route `/operations/energy` | client-side routing | ✅ |
| 11 | React analytics MFE bundle served (`/analytics-mfe/analytics-mfe.js`, >100 kB) | MFE packaged into portal | ✅ |
| 12 | Runtime BFF URL injected into `/appsettings.json` | `PORTAL_BFF_BASE_URL`/`BFF_BASE_URL` rewrite | ✅ |
| 13 | `.wasm` served as `application/wasm` | Blazor WASM MIME | ✅ |

---

## 4. Additional image-level checks (`docker image inspect` / runtime)

| Requirement | Evidence | Result |
|---|---|---|
| Port 8080 | BFF `ExposedPorts: 8080/tcp`, CMD `uvicorn … --port 8080`; Portal `listen 8080` + `ExposedPorts` includes `8080/tcp` | ✅ |
| Health probes | BFF `HEALTHCHECK` → `python … urlopen('http://localhost:8080/health/live')`; Portal `HEALTHCHECK` → `wget … /healthz` | ✅ |
| Immutable tags/digests | Timestamped deploy tag + `RepoDigests` `…@sha256:…` present for both images | ✅ |
| Non-root (BFF) | `USER app`; runtime `uid=999 euid=999 user=app` | ✅ |
| Runtime safety (Portal) | nginx `user nginx;` drops worker privileges; listens on non-privileged 8080; `server_tokens off` | ✅ |
| Protected Python feed baked | `/etc/pip.conf` + `PIP_INDEX_URL` = protected feed, **no** `extra-index-url` | ✅ |
| Protected NuGet feed | `NuGet.Config` clears sources → single protected feed; restore/publish succeeded | ✅ |
| Runtime BFF URL injection | `/docker-entrypoint.d/20-novasteel-inject-bff-url.sh` rewrites `appsettings.json` `Bff:BaseUrl` (validated live in test 12) | ✅ |
| CORS restricted to portal origin | validated live in tests 5–6 | ✅ |
| Deterministic demo endpoints | validated live in tests 3, 4, 7 | ✅ |

---

## 5. Packaging fix applied (owned file)

**`.azure\scripts\test-images.ps1`** — the `Get-Http` helper crashed the entire
run on its first request (`Smoke tests: 0 passed, 0 failed`). Under
`Set-StrictMode -Version Latest`, the catch block read `$_.Exception.Response`,
but the exception raised while the container is still starting
(`HttpRequestException`/`TaskCanceledException`) has **no** `Response` property, so
strict mode threw `PropertyNotFoundException` before the readiness retry loop
could succeed.

Fix (behavior-preserving): probe for the property before reading it.

```powershell
$response = if ($_.Exception -and $_.Exception.PSObject.Properties['Response']) { $_.Exception.Response } else { $null }
if ($response -and $response.PSObject.Properties['StatusCode'] -and $null -ne $response.StatusCode) {
    $code = [int]$response.StatusCode
}
```

Empirically confirmed the connection-failure exception lacks `Response` (so the
guard returns `$null`) and that dictionary missing-key indexing (CORS-reject /
header lookups) returns `$null` safely under strict mode, so no other lines
needed changing. Re-run after the fix: **13/13 pass**.

---

## 6. Non-blocking observations (no action required)

- **BuildKit lint `SecretsUsedInArgOrEnv` on BFF Dockerfile line 58 (`ENV BFF_AUTH_MODE`)** —
  false positive (value is the literal `demo`, a mode flag, not a secret). Build
  is not failed; the ENV is a required deterministic-demo default the runtime
  reads. Left unchanged intentionally.
- **Portal image exposes `80/tcp` in addition to `8080/tcp`** — `80` is inherited
  `EXPOSE` metadata from `nginx:1.27-alpine`; nothing listens on it (config only
  `listen 8080;`). Container Apps ingress targets 8080. Harmless metadata only.

---

## 7. Blockers

**None.** Both protected feeds were reachable
(`packagefeedproxy.microsoft.io` pypi GET 200, nuget index 200), images built and
passed every check. No image was pushed or deployed (packaging validation only).

---

## 8. Reproduce

```powershell
# 1) Feed/security scan (covers Dockerfiles)
python tools\validation\verify_protected_feeds.py --root . --json artifacts\validation\protected-feeds.json
python tools\validation\security_scan.py         --root . --json artifacts\validation\security.json

# 2) Build both images (immutable tag, local --load, no push)
pwsh .\.azure\scripts\build-images.ps1

# 3) Smoke test both images
pwsh .\.azure\scripts\test-images.ps1

# 4) Image-level assertions
docker image inspect novasteelv3/bff:local novasteelv3/portal:local
docker run --rm novasteelv3/bff:local python -c "import os;print(os.getuid())"          # -> 999 (non-root)
docker run --rm --entrypoint sh novasteelv3/bff:local -c "cat /etc/pip.conf"            # protected feed, no extra-index-url
```
