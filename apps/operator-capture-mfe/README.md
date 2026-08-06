# operator-capture-mfe

Installable, mobile-first **PWA that lets a shop-floor operator record a procedure by voice** and file it
into the Knowledge Hub as a `DRAFT` awaiting human approval.

It is a standalone app rather than a screen inside `analytics-mfe`: the operator persona works one-handed
on a phone at the furnace, not at a desk, and needs the app to survive a flaky network.

## Flow

1. **Consent gate** — GDPR Art. 6(1)(a) consent + retention period. Recording controls stay disabled until
   consent is granted, mirroring the wording already used in the Knowledge Hub capture dialog.
2. **Record** — `getUserMedia` + `MediaRecorder`, large thumb-reachable controls, live elapsed timer and
   input-level meter, pause/resume, auto-pause when the tab is backgrounded. **Or import an existing audio
   file** instead (see below).
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

## Importing an audio file

Not every procedure is captured live: handovers get recorded on a plant dictaphone, and some tablets have
no usable microphone at all. The record step therefore also offers **Import an audio file**, which feeds the
file into exactly the same review → upload → transcript → draft path as a live recording. The import
affordance is shown even when the recorder reports `unsupported` or a permission error, because that is
precisely when an operator needs it.

`src/audio/audioFile.ts` normalises the file before it is accepted:

- Content types are folded onto the five the BFF allows (`audio/webm`, `audio/ogg`, `audio/wav`,
  `audio/mpeg`, `audio/mp4`). The same `.wav` arrives as `audio/wav`, `audio/x-wav` or `audio/wave`
  depending on the platform, and iOS often reports `application/octet-stream`, in which case the filename
  extension decides.
- Non-audio, empty and over-25 MB files are refused in the browser rather than after a long upload.
- Duration is probed from a detached media element for the review screen, defaulting to 0 rather than
  failing the import if the browser cannot read the header.

### Sample interview

`public/samples/blast-furnace-hearth-cooling-en.wav` (~68 s, 16 kHz mono) ships with the app and is
reachable from the record step via **Load the sample interview**, so the whole flow can be demonstrated
without a microphone or a quiet room.

It narrates `services/knowledge-orchestrator/fixtures/interview_transcript.json` verbatim — the same
fixture the backend returns when it transcribes in demo mode — so the transcript you see afterwards matches
the audio you just heard. The interview is synthetic (fictional persona OP-DEMO-014, blast-furnace hearth
cooling) and contains no real personal data.

Regenerate it with `pwsh -File scripts/generate-sample-audio.ps1` after editing the fixture, so audio and
transcript never drift apart.

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
