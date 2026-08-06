# operator-capture-mfe

Installable, mobile-first **PWA that lets a shop-floor operator record a procedure by voice** and file it
into the Knowledge Hub as a `DRAFT` awaiting human approval.

It is a standalone app rather than a screen inside `analytics-mfe`: the operator persona works one-handed
on a phone at the furnace, not at a desk, and needs the app to survive a flaky network.

## Flow

1. **Consent gate** — GDPR Art. 6(1)(a) consent + retention period. Recording controls stay disabled until
   consent is granted, mirroring the wording already used in the Knowledge Hub capture dialog.
2. **Record** — `getUserMedia` + `MediaRecorder`, large thumb-reachable controls, live elapsed timer and
   input-level meter, pause/resume, auto-pause when the tab is backgrounded.
3. **Review** — local playback and discard/retake. Nothing leaves the device until the operator confirms.
4. **Upload** — multipart upload with progress, cancel and retry. A failed upload is persisted to
   **IndexedDB** so a recording is never silently lost.
5. **Transcript** — polls the transcript endpoint with backoff, honouring the `PROCESSING` state, then
   shows segments with speaker and confidence.
6. **Store** — creates the `DRAFT` procedure and offers *Submit for review*.

## Human-in-the-loop

The operator can capture and submit for review. **Only `Knowledge.Publisher` can approve or reject**, so
nothing an operator records becomes an operational instruction without a domain expert signing off — see
`docs/tech/api-contracts.md` §4.7 and §10.3.

## API surface consumed

| Call | Purpose |
| --- | --- |
| `POST /v1/knowledge/interviews` | Create the consent-bound session |
| `POST /v1/knowledge/interviews/{id}/audio` | Upload the recording (multipart, 25 MB cap) |
| `GET /v1/knowledge/interviews/{id}/transcript` | Poll for the transcript |
| `POST /v1/knowledge/interviews/{id}/draft` | Create the `DRAFT` procedure |
| `POST /v1/knowledge/procedures/{id}:submit` | Move the draft to `IN_REVIEW` |

## PWA behaviour

`public/service-worker.js` is hand-written (no build plugin). It caches the app shell so the UI loads on a
weak shop-floor network, and **explicitly bypasses every `/v1/knowledge/` request** — audio and transcript
traffic is `Highly Confidential` and is never written to the cache.

## Deployment

The app ships as its own container (nginx serving the static Vite bundle on port `8080`) and its own
Azure Container App, `novasteelv3-capture`, alongside the portal and BFF.

**Demo URL:** <https://novasteelv3-capture.calmbeach-dbad72b1.swedencentral.azurecontainerapps.io>

| Piece | Where |
| --- | --- |
| Image build | `Dockerfile` (BuildKit named contexts `reporoot` + `contracts`) |
| Runtime server | `runtime/nginx.conf` |
| Runtime config | `runtime/inject-config.sh` |
| Local build | `.azure/scripts/build-images.ps1 -Target capture`, or the `capture` bake target |
| Infrastructure | `.azure/infra/modules/apps.bicep` (`captureImage` / `captureOrigin` / `captureBffBaseUrl`) |
| CI build + CD | `.github/workflows/ci-build-services.yml` -> `cd-services.yml` (`operator-capture-mfe`) |

Pushing a change under `apps/operator-capture-mfe/**` to `main` builds the image, pushes it to ACR by
immutable digest and promotes it to the demo Container App automatically.

### Runtime configuration

The BFF origin is **not** baked into the bundle. `runtime/inject-config.sh` writes `/config.js` on
container start from the `CAPTURE_BFF_BASE_URL` (or `BFF_BASE_URL`) environment variable, and
`index.html` loads it before the app bundle. One image is therefore promotable across environments.
With no BFF URL set the app falls back to synthetic demo mode instead of calling its own static origin.

`nginx.conf` marks `config.js` and `service-worker.js` `no-store`/`no-cache`, and the service worker
skips `config.js`, so a redeploy can never be pinned to a previous environment's backend.

### CORS and identity

The PWA is served from its own origin, so the BFF must allowlist it. `apps.bicep` appends
`captureOrigin` to `BFF_CORS_ORIGINS`; without that every capture call fails in the browser.

In demo auth mode the BFF also requires a **plant scope**: a demo identity with no `X-Demo-Plants`
header (or a value outside `NS-DEMO-*`) is rejected with `401`. `src/config.ts` always sends it, and
`src/config.test.ts` guards the regression.

## Commands

Run from the repo root (npm workspace) or from this folder:

```powershell
npm --workspace @novasteel/operator-capture-mfe run dev
npm --workspace @novasteel/operator-capture-mfe run test
npm --workspace @novasteel/operator-capture-mfe run lint
npm run build:capture
```

## Notes

- Dependency versions are pinned to match `analytics-mfe` (React 19.2.7, MUI 9.2.0, Vite 8.1.5).
- Packages resolve only through the Microsoft-protected npm feed — see `.npmrc` and
  `docs/tech/security_requirement.md`.
- i18n covers `en`, `fr`, `de`, `nl`, `es`.
- Demo mode short-circuits the client to synthetic data so the app is demoable without a live backend.
